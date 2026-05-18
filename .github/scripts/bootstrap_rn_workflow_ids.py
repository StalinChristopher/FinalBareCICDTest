#!/usr/bin/env python3
"""
Rewrite template-specific iOS/Android identifiers in .github/workflows after
copying this kit into another React Native repository.

Run from the target app root (where android/ and optionally ios/ live).

Examples:
  python3 .github/scripts/bootstrap_rn_workflow_ids.py --dry-run
  python3 .github/scripts/bootstrap_rn_workflow_ids.py
  python3 .github/scripts/bootstrap_rn_workflow_ids.py --workspace ios/MyApp.xcworkspace --scheme MyApp \\
      --bundle-id-dev com.example.app.dev --bundle-id-dist com.example.app
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Template literals shipped with this kit (replace in workflow YAML only).
OLD_WS = "ios/TemplatePipelineReactNative.xcworkspace"
OLD_XCODEPROJ = "ios/TemplatePipelineReactNative.xcodeproj"
OLD_BUILD_IPA = "build/template-pipeline-react-native.ipa"
OLD_IPA_FILENAME = "template-pipeline-react-native.ipa"
OLD_SCHEME = "TemplatePipelineReactNative"
OLD_SCHEME_PROD = "TemplatePipelineReactNative_prod"
OLD_BUNDLE_DEV = "com.codeandtheory.edward-jones-poc.dev"
OLD_BUNDLE_DIST = "com.codeandtheory.edward-jones-poc.dist"
OLD_ARTIFACT = "TemplatePipelineReactNative-iphonesimulator-Debug"


def find_ios_workspaces(ios_dir: Path) -> list[Path]:
    return sorted(p for p in ios_dir.glob("*.xcworkspace") if p.is_dir())


def find_app_xcodeproj(ios_dir: Path, workspace_stem: str) -> Path | None:
    candidates = [p for p in ios_dir.glob("*.xcodeproj") if p.is_dir() and not p.name.startswith("Pods")]
    if not candidates:
        return None
    for p in candidates:
        if p.stem == workspace_stem:
            return p
    if len(candidates) == 1:
        return candidates[0]
    return None


def list_shared_schemes(xcodeproj: Path) -> list[str]:
    schemes_dir = xcodeproj / "xcshareddata" / "xcschemes"
    if not schemes_dir.is_dir():
        return []
    names: list[str] = []
    for f in sorted(schemes_dir.glob("*.xcscheme")):
        if f.name.startswith("Pods-"):
            continue
        names.append(f.stem)
    return names


def pick_schemes(scheme_names: list[str], proj_stem: str) -> tuple[str, str]:
    """Return (dev_scheme, prod_scheme)."""
    if not scheme_names:
        raise ValueError("No shared .xcscheme files under xcshareddata/xcschemes")

    prod_candidates = [s for s in scheme_names if s.endswith("_prod") or s.endswith("Prod")]
    dev_candidates = [s for s in scheme_names if s not in prod_candidates]

    prod = None
    if prod_candidates:
        for s in prod_candidates:
            if s.startswith(proj_stem):
                prod = s
                break
        prod = prod or prod_candidates[0]

    dev = None
    for s in dev_candidates:
        if s == proj_stem:
            dev = s
            break
    if dev is None and dev_candidates:
        dev = dev_candidates[0]
    if dev is None:
        dev = scheme_names[0]

    if prod is None:
        guess = f"{dev}_prod"
        if guess in scheme_names:
            prod = guess
        else:
            prod = dev

    return dev, prod


def bundle_ids_from_pbxproj(pbxproj: Path) -> tuple[str | None, str | None]:
    text = pbxproj.read_text(encoding="utf-8", errors="replace")
    found: list[str] = []
    for m in re.finditer(
        r"PRODUCT_BUNDLE_IDENTIFIER\s*=\s*(?:\"([^\"]+)\"|([^;\s]+)\s*;)",
        text,
    ):
        val = (m.group(1) or m.group(2) or "").strip()
        if not val or "Tests" in val:
            continue
        if val not in found:
            found.append(val)

    dev = next((b for b in found if b.endswith(".dev") or ".dev" in b), None)
    dist = next((b for b in found if b.endswith(".dist") or ".dist" in b), None)
    if dev and not dist and len(found) == 2:
        dist = next((b for b in found if b != dev), None)
    if not dev and found:
        dev = found[0]
    if not dist and len(found) > 1:
        dist = next((b for b in found if b != dev), None)
    return dev, dist


def read_android_build_gradle(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    kts = path.with_suffix(".gradle.kts")
    if kts.is_file():
        return kts.read_text(encoding="utf-8", errors="replace")
    raise FileNotFoundError(f"Missing {path} and {kts}")


def android_has_dev_flavor(content: str) -> bool:
    return bool(re.search(r"productFlavors\s*\{[\s\S]*?\bdev\s*\{", content))


def android_dev_application_id(content: str) -> str | None:
    m = re.search(
        r"\bdev\s*\{[\s\S]*?applicationId\s+[\"']([^\"']+)[\"']",
        content,
        re.MULTILINE,
    )
    return m.group(1).strip() if m else None


def apply_replacements(text: str, mapping: list[tuple[str, str]]) -> str:
    for old, new in mapping:
        if old != new:
            text = text.replace(old, new)
    return text


def replace_in_workflows(workflow_dir: Path, mapping: list[tuple[str, str]], dry_run: bool) -> list[str]:
    changed: list[str] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        orig = text
        text = apply_replacements(text, mapping)
        if text != orig:
            changed.append(path.name)
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return changed


def patch_fastfile(root: Path, mapping: list[tuple[str, str]], dry_run: bool) -> bool:
    """Rewrite ios/*.xcodeproj, workspace, and IPA paths in fastlane/Fastfile if present."""
    path = root / "fastlane" / "Fastfile"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    orig = text
    text = apply_replacements(text, mapping)
    if text == orig:
        return False
    if not dry_run:
        path.write_text(text, encoding="utf-8")
    return True


def patch_android_ci_snippets(
    workflow_dir: Path,
    gradle_task: str,
    artifact_glob: str,
    dry_run: bool,
) -> list[str]:
    """Replace assembleDevRelease + dev APK glob in rn.yml and rn-firebase-release.yml."""
    touched: list[str] = []
    targets = ("rn.yml", "rn-firebase-release.yml")
    for name in targets:
        path = workflow_dir / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        orig = text
        text = re.sub(r"gradle_task:\s*assembleDevRelease\b", f"gradle_task: {gradle_task}", text)
        text = re.sub(
            r"artifact_glob:\s*app/build/outputs/apk/dev/release/\*\.apk\b",
            f"artifact_glob: {artifact_glob}",
            text,
        )
        if text != orig:
            touched.append(name)
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return touched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    ap.add_argument("--workspace", help=f"Relative path to .xcworkspace (default: auto-detect under ios/).")
    ap.add_argument("--scheme", help="Main iOS scheme for dev/Debug (default: auto-detect).")
    ap.add_argument("--ios-scheme-prod", help="iOS scheme for prod/dist (default: {scheme}_prod or same as scheme).")
    ap.add_argument("--bundle-id-dev", help="iOS dev / simulator bundle id (default: from Xcode project).")
    ap.add_argument("--bundle-id-dist", help="iOS distribution bundle id (default: infer or copy dev).")
    ap.add_argument(
        "--gradle-task",
        help="Gradle task for dev Android Firebase job (default: assembleDevRelease if dev flavor exists, else assembleRelease).",
    )
    ap.add_argument(
        "--apk-glob",
        help="APK glob for dev Android Firebase job (default matches --gradle-task).",
    )
    args = ap.parse_args()

    root = Path.cwd()
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        print("error: .github/workflows not found — run from app repository root", file=sys.stderr)
        return 1

    ios_dir = root / "ios"
    if not ios_dir.is_dir():
        print(
            "error: ios/ not found — generate native projects (e.g. expo prebuild) or pass explicit --workspace/--scheme/--bundle-id-*",
            file=sys.stderr,
        )
        return 1

    if args.workspace:
        ws_rel = args.workspace.strip().lstrip("./")
        ws_path = root / ws_rel
        if not ws_path.is_dir():
            print(f"error: workspace not found: {ws_path}", file=sys.stderr)
            return 1
        ws_stem = ws_path.stem
    else:
        wss = find_ios_workspaces(ios_dir)
        if len(wss) != 1:
            print(
                "error: expected exactly one ios/*.xcworkspace; use --workspace\n"
                f"  found: {[p.name for p in wss]}",
                file=sys.stderr,
            )
            return 1
        ws_path = wss[0]
        ws_rel = str(ws_path.relative_to(root))
        ws_stem = ws_path.stem

    xcodeproj = find_app_xcodeproj(ios_dir, ws_stem)
    if xcodeproj is None:
        print("error: could not locate app .xcodeproj under ios/", file=sys.stderr)
        return 1

    scheme_names = list_shared_schemes(xcodeproj)
    try:
        auto_dev, auto_prod = pick_schemes(scheme_names, xcodeproj.stem)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    scheme_dev = args.scheme or auto_dev
    scheme_prod = args.ios_scheme_prod or auto_prod

    pbx = xcodeproj / "project.pbxproj"
    b_dev_auto, b_dist_auto = bundle_ids_from_pbxproj(pbx)
    bundle_dev = args.bundle_id_dev or b_dev_auto
    bundle_dist = args.bundle_id_dist or b_dist_auto
    if not bundle_dev:
        print("error: could not infer bundle id — pass --bundle-id-dev", file=sys.stderr)
        return 1
    if not bundle_dist:
        if bundle_dev.endswith(".dev"):
            bundle_dist = bundle_dev[: -len(".dev")]
        else:
            bundle_dist = bundle_dev

    gradle_path = root / "android" / "app" / "build.gradle"
    gradle_task = args.gradle_task
    apk_glob = args.apk_glob
    try:
        gtext = read_android_build_gradle(gradle_path)
    except FileNotFoundError:
        gtext = ""
    has_dev = android_has_dev_flavor(gtext) if gtext else False
    if not gradle_task:
        gradle_task = "assembleDevRelease" if has_dev else "assembleRelease"
    if not apk_glob:
        apk_glob = (
            "app/build/outputs/apk/dev/release/*.apk"
            if has_dev
            else "app/build/outputs/apk/release/*.apk"
        )

    artifact_name = f"{scheme_dev}-iphonesimulator-Debug"
    new_xcodeproj_rel = f"ios/{ws_stem}.xcodeproj"
    ipa_filename = f"{ws_stem}.ipa"

    # Longest / most specific strings first so we do not partially replace inside paths.
    mapping: list[tuple[str, str]] = [
        (OLD_WS, ws_rel),
        (OLD_XCODEPROJ, new_xcodeproj_rel),
        (OLD_BUILD_IPA, f"build/{ipa_filename}"),
        (OLD_IPA_FILENAME, ipa_filename),
        (OLD_SCHEME_PROD, scheme_prod),
        (OLD_ARTIFACT, artifact_name),
        (OLD_BUNDLE_DEV, bundle_dev),
        (OLD_BUNDLE_DIST, bundle_dist),
        (OLD_SCHEME, scheme_dev),
    ]

    print("Detected / using:")
    print(f"  ios_workspace: {ws_rel}")
    print(f"  ios_scheme (dev): {scheme_dev}")
    print(f"  ios_scheme (prod): {scheme_prod}")
    print(f"  bundle_id_dev: {bundle_dev}")
    print(f"  bundle_id_dist: {bundle_dist}")
    print(f"  android_dev gradle_task: {gradle_task}")
    print(f"  android_dev artifact_glob: {apk_glob}")
    if gtext:
        aid = android_dev_application_id(gtext)
        if aid:
            print(f"  android dev applicationId (gradle): {aid}")

    changed = replace_in_workflows(wf_dir, mapping, args.dry_run)
    android_touched = patch_android_ci_snippets(wf_dir, gradle_task, apk_glob, args.dry_run)
    fastlane_touched = patch_fastfile(root, mapping, args.dry_run)

    mode = "Would update" if args.dry_run else "Updated"
    print(f"\n{mode} workflow files (string replacements): {', '.join(changed) or '(none)'}")
    print(f"{mode} Android CI snippets: {', '.join(android_touched) or '(none)'}")
    print(f"{mode} fastlane/Fastfile: {'yes' if fastlane_touched else '(unchanged or missing)'}")

    if args.dry_run and (changed or android_touched or fastlane_touched):
        print("\nRe-run without --dry-run to apply.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
