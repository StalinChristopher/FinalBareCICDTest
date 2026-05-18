# Reuse this template’s GitHub Actions in another React Native repo

This document is the linear guide for copying **CI infrastructure** from [this repository](../README.md) into an existing **bare** or **Expo (prebuild)** app.

## Prerequisites

- Target repo root contains `package.json` and `android/`. **Bare** and **Expo** paths in [`rn.yml`](../.github/workflows/rn.yml) both use the **same** Gradle + Fastlane jobs and require a committed **`ios/`** tree for iOS. **Expo:** CI does **not** run `expo prebuild`; you must run **`npx expo prebuild --clean`** locally (with the correct `APP_ENV` / flavor), then **commit `android/` and `ios/`**. The **`expo-native-dirs`** job fails fast if those directories are missing. Re-run prebuild and commit after SDK upgrades, new native modules, or `app.config` / plugin changes that affect native code.
- **Node 20** (see `engines` in the template `package.json`). Workflows use Node 20 on GitHub-hosted runners.
- **GitHub Actions** enabled on the target repository.

## iOS toolchain (Xcode)

Reusable **macOS** iOS jobs in this template pin **Xcode 26.2** (`maxim-lobanov/setup-xcode` and workflow `env.XCODE_VERSION`). That matches **Expo SDK 55** expectations (minimum **Xcode 26**; EAS defaults to **26.2**) and applies to **bare and Expo** apps the same way—there is no separate Xcode version per build system.

**Do not** set job-level `DEVELOPER_DIR` to `/Applications/Xcode.app/Contents/Developer` when using `setup-xcode` to select another app bundle (for example `Xcode_26.2.app`). Forcing `DEVELOPER_DIR` to the default `Xcode.app` path while `xcode-select` points elsewhere makes `xcodebuild` / CocoaPods / Fastlane use a **mixed** toolchain and can surface Swift compile errors in **`expo-modules-core`** (for example unknown `@MainActor` attributes). Let `setup-xcode` control the active developer directory.

If GitHub’s `macos-15` image drops **26.2** but ships **26.3**, bump the pin in every `rn-job-ios-*.yml` that calls `setup-xcode` so the string matches an installed Xcode on the runner ([runner-images](https://github.com/actions/runner-images)).

## One-shot apply (Cursor Agent)

1. Open the **target** app in Cursor (folder that has `package.json`).
2. **Preferred:** After the first `rsync` of [`.cursor/`](../.cursor/) from this template, the target repo contains [`.cursor/skills/rn-devops-apply-kit/SKILL.md`](../.cursor/skills/rn-devops-apply-kit/SKILL.md). Ask the agent to follow that skill for a **low-token, shell-first** run (user supplies **`PATH:`** or **`TEMPLATE_ROOT`** to the template clone, optional **`TARGET_REMOTE_URL`**, optional bootstrap flags — see the skill’s input table and [Recommended (minimal)](#recommended-minimal) below).
3. **Fallback:** In the **template** clone, open [`CURSOR_RN_DEVOPS_ONE_SHOT_APPLY.txt`](../CURSOR_RN_DEVOPS_ONE_SHOT_APPLY.txt), fill in the same inputs, and paste from the line after the `ONE-SHOT` banner through **END ONE-SHOT** when repo skills are not available to the agent.

The agent should: `rsync` [`.github/`](../.github/), [`.semgrep/`](../.semgrep/), [`.cursor/`](../.cursor/) per [`SETUP_RN_DEVOPS_KIT.md`](../SETUP_RN_DEVOPS_KIT.md) (including copying root **`Gemfile`** / **`Gemfile.lock`** and **`fastlane/Fastfile`** when missing, or with explicit overwrite if the user confirms), merge [`GITIGNORE_APPEND.txt`](../GITIGNORE_APPEND.txt) lines, align `package.json` scripts, run [`bootstrap_rn_workflow_ids.py`](../.github/scripts/bootstrap_rn_workflow_ids.py), optionally run [`assert_expo_native_dirs.sh`](../.github/scripts/assert_expo_native_dirs.sh) for Expo apps, and generate `GITHUB_SECRETS_CHECKLIST.md` via [`list_workflow_secrets.py`](../.github/scripts/list_workflow_secrets.py).

### What to type in the target app

**Workspace:** Cursor must be opened on the **target app** (repo root with `package.json`). You do not need the template repo as the workspace.

**Where `rn-devops-apply-kit` lives:** **`<template-clone>/.cursor/skills/rn-devops-apply-kit/SKILL.md`**. After the first `rsync` of `.cursor/` from the template, the same path exists under **`<your-app>/.cursor/skills/rn-devops-apply-kit/SKILL.md`**. The agent follows that playbook. You may `@`-mention the file if your Cursor build supports it.

#### Recommended (minimal)

```text
Apply the RN DevOps kit to this target repo.
PATH: /absolute/path/to/template-pipeline-react-native
```

Replace the path with your **template-pipeline-react-native** clone (**no trailing slash**). The agent treats **`PATH:`** as **`TEMPLATE_ROOT`** (see [`.cursor/skills/rn-devops-apply-kit/SKILL.md`](../.cursor/skills/rn-devops-apply-kit/SKILL.md)). Same message is optional: **`TARGET_REMOTE_URL=…`**; for wrong bootstrap detection add flags per [Bootstrap script flags](#bootstrap-script-flags).

#### Advanced (long prompts and older variants)

The blocks below are optional—for teams that prefer explicit step lists, `TEMPLATE_ROOT=…` syntax, or skill-first ordering.

##### Single message (skill on disk, then full apply)

**When you want one paste and no second message:** the agent runs Phase 0 (copy skill + rules), optionally `read_file` this repo’s `./.cursor/skills/rn-devops-apply-kit/SKILL.md`, then completes Phases 1–8 in the same session (full `.github/` / `.semgrep/` / `.cursor/` rsync in Phase 2 stays idempotent). See the skill file section **Single session (one user message)** for the authoritative steps.

Paste (set **`PATH:`** first line or last line; agent exports **`TEMPLATE_ROOT`** from it, then runs Phase 0):

```text
Apply the RN DevOps kit in ONE agent session with no second message from me.

PATH: /absolute/path/to/template-pipeline-react-native

1) Export TEMPLATE_ROOT from PATH above, then: mkdir -p .cursor/skills .cursor/rules; rsync -a "${TEMPLATE_ROOT}/.cursor/skills/rn-devops-apply-kit/" "./.cursor/skills/rn-devops-apply-kit/"; rsync -a "${TEMPLATE_ROOT}/.cursor/rules/" "./.cursor/rules/"
2) read_file ./.cursor/skills/rn-devops-apply-kit/SKILL.md once, then execute Phases 1–8 from that skill (including full rsync of .github, .semgrep, .cursor in Phase 2). Shell-first; do not wait for another user message.
```

Optional lines (same message): `TARGET_REMOTE_URL=…`; bootstrap hint pointing to [Bootstrap script flags](#bootstrap-script-flags).

##### First apply (no `.cursor/` in the app yet)

The Cursor skill may not be discoverable until `.github/` and `.cursor/` are copied. Paste something like:

```text
Apply the RN DevOps kit using the same phases and rules as rn-devops-apply-kit (template-pipeline-react-native .cursor/skills/rn-devops-apply-kit/SKILL.md): shell-first, do not bulk-read workflows into chat.

PATH: /absolute/path/to/template-pipeline-react-native
```

Or legacy: `TEMPLATE_ROOT=/absolute/path/to/template-pipeline-react-native`

Optional lines:

```text
TARGET_REMOTE_URL=git@github.com:org/my-app.git
```

```text
Bootstrap (only if dry-run is wrong): append e.g. --bundle-id-dist com.example.app.dist to bootstrap_rn_workflow_ids.py — see docs/RN_WORKFLOW_REUSE.md#bootstrap-script-flags
```

**Full fallback:** paste the entire block from [`CURSOR_RN_DEVOPS_ONE_SHOT_APPLY.txt`](../CURSOR_RN_DEVOPS_ONE_SHOT_APPLY.txt) (from the line after the `ONE-SHOT` banner through **END ONE-SHOT**).

##### After `.cursor/` exists in the target (subsequent runs)

Shorter prompt; a path line is still required whenever you re-run **`rsync`** of `.github/` / `.semgrep/` / `.cursor/` from the template:

```text
Follow rn-devops-apply-kit for this repo.
PATH: /absolute/path/to/template-pipeline-react-native
```

If the kit is already copied and you only need to re-bootstrap or refresh secrets, say so explicitly (e.g. “skip rsync; run bootstrap dry-run then real, then list_workflow_secrets”) and pass any bootstrap flags per [Bootstrap script flags](#bootstrap-script-flags).

## Manual copy (terminal only)

From the **target** repo root:

```bash
TEMPLATE_ROOT="/absolute/path/to/template-pipeline-react-native"

rsync -a --delete "${TEMPLATE_ROOT}/.github/" "./.github/"
rsync -a "${TEMPLATE_ROOT}/.semgrep/" "./.semgrep/"
rsync -a "${TEMPLATE_ROOT}/.cursor/" "./.cursor/"

if [ ! -f ./Gemfile ] || [ ! -f ./Gemfile.lock ]; then
  cp "${TEMPLATE_ROOT}/Gemfile" "${TEMPLATE_ROOT}/Gemfile.lock" ./
fi

if [ ! -f ./fastlane/Fastfile ]; then
  mkdir -p fastlane
  cp "${TEMPLATE_ROOT}/fastlane/Fastfile" ./fastlane/
fi
```

Append missing lines from the template’s [`GITIGNORE_APPEND.txt`](../GITIGNORE_APPEND.txt) to `.gitignore`.

Then run (still from target root):

```bash
python3 .github/scripts/bootstrap_rn_workflow_ids.py --dry-run
python3 .github/scripts/bootstrap_rn_workflow_ids.py
python3 .github/scripts/list_workflow_secrets.py --write GITHUB_SECRETS_CHECKLIST.md
```

If bootstrap fails (no `ios/`, multiple workspaces, wrong schemes), pass explicit flags — see **Bootstrap script flags** below.

## `package.json` scripts required by CI

These commands must exist (add scripts and devDependencies as needed):

| Script | Typical command |
| --- | --- |
| `lint` | `eslint .` |
| `format:check` | `prettier --check "src/**/*.{ts,tsx,js}"` (adjust globs if your code is not under `src/`) |
| `typecheck` | `tsc --noEmit` |
| `test:ci` | `jest --ci --coverage --maxWorkers=2` |

The orchestrator passes an **80%** Jest coverage threshold to [`rn-job-js-test.yml`](../.github/workflows/rn-job-js-test.yml). Lower it in `rn.yml` if needed.

## Yarn-only repos and `setup-node` cache

[`install_js_deps.sh`](../.github/scripts/install_js_deps.sh) already picks **yarn** when `yarn.lock` exists. Some reusable workflows still use:

```yaml
cache: npm
cache-dependency-path: package-lock.json
```

If the target repo has **only** `yarn.lock` (no `package-lock.json`), either:

- add a `package-lock.json` (e.g. run `npm install` once and commit — not ideal for yarn-first teams), or  
- edit the affected workflow files under `.github/workflows/` to use `cache: yarn` and `cache-dependency-path: yarn.lock` for `actions/setup-node` steps (search for `cache-dependency-path`).

## Expo vs bare (`rn.yml`)

| Condition | `detect` output |
| --- | --- |
| `package.json` lists **`expo`** in `dependencies` or `devDependencies` | `expo` |
| otherwise | `bare` |
| Manual `workflow_dispatch` | `build_system` input: **`auto`**, **`bare`**, or **`expo`** |

### Bare (`detect` = `bare`)

- **iOS in `rn.yml`:** runs **`ios-dev`** only (see next bullet). Reusable workflows [`rn-job-ios-simulator-artifact.yml`](../.github/workflows/rn-job-ios-simulator-artifact.yml) and [`rn-job-ios-test.yml`](../.github/workflows/rn-job-ios-test.yml) are **not** invoked by the default orchestrator unless you add them.
- **Android / iOS dev:** [`android-dev` / `ios-dev`](../.github/workflows/rn.yml) use Gradle + Fastlane; **pull_request** = workflow artifacts only; **push** to `main` / `master` / `development` = **Firebase App Distribution**.

### Expo (`detect` = `expo`)

- **Same** [`android-dev` / `ios-dev`](../.github/workflows/rn.yml) jobs as bare: signed builds on **GitHub runners** (Ubuntu + macOS), then **Firebase** on push. **No EAS Build** and **no `EXPO_TOKEN`** in this orchestrator.
- **Committed native projects:** before native jobs, **`expo-native-dirs`** checks for `android/app/build.gradle`, `ios/Podfile`, and at least one `ios/*.xcodeproj`. If anything is missing, the workflow fails with instructions to run **`npx expo prebuild --clean`**, then commit **`android/`** and **`ios/`**.
- **Gradle / scheme / bundle ID:** Expo single-flavor apps often need **`assembleRelease`** and a matching APK glob in `rn.yml` (not `assembleDevRelease`). Run [`bootstrap_rn_workflow_ids.py`](../.github/scripts/bootstrap_rn_workflow_ids.py) after local prebuild so `app_identifier`, `ios_scheme`, and Android task/glob match your generated project.

#### Signing and secrets (Expo in `rn.yml`)

- Same as **bare**: **`RELEASE_KEYSTORE_*`**, **`DIST_*`** / dev iOS signing secrets, **Firebase** service account and app IDs. Configure signing in Apple Developer / your keystore, not via EAS for this path.

#### Other workflows (manual Firebase / internal release)

- [`rn-firebase-release.yml`](../.github/workflows/rn-firebase-release.yml) and [`rn-internal-release.yml`](../.github/workflows/rn-internal-release.yml) use the same **`auto` \| `bare` \| `expo`** detection as **`rn.yml`** (`expo` when **`package.json`** lists **`expo`**). Expo apps use the **same** Gradle + Fastlane reusable jobs as bare, with **`expo-native-dirs`** asserting committed native projects. **EAS**-centric reusable jobs (e.g. `rn-job-*-internal-release-expo.yml`) remain in the kit for optional custom wiring but are **not** invoked from these orchestrators.

## Bootstrap script flags

[`bootstrap_rn_workflow_ids.py`](../.github/scripts/bootstrap_rn_workflow_ids.py) updates template defaults in `.github/workflows/*.yml` and patches **`fastlane/Fastfile`** when present.

**Where iOS bundle IDs come from:** the script scans **`ios/<app>.xcodeproj/project.pbxproj`** for **`PRODUCT_BUNDLE_IDENTIFIER`** and replaces the kit’s placeholder dev/dist bundle IDs. Commit **`ios/`** after **`expo prebuild`** so those values match your app. The scaffold / **`app.config.ts`** is not read here—only the Xcode project on disk. If every build configuration uses the same **`.dev`** id and you still need a distinct **`.dist`** string in workflows (signing, Firebase dist), pass **`--bundle-id-dist`** explicitly; otherwise dist may be inferred as the base id with **`.dev`** stripped.

| Flag | When to use |
| --- | --- |
| `--workspace ios/MyApp.xcworkspace` | More than one `ios/*.xcworkspace` |
| `--scheme MyApp` | Ambiguous or wrong auto-selected scheme |
| `--ios-scheme-prod MyApp_prod` | Prod scheme name differs from `{scheme}_prod` |
| `--bundle-id-dev` / `--bundle-id-dist` | Override inferred IDs from `project.pbxproj`; use **`--bundle-id-dist`** when no `*.dist` appears in the Xcode project but Firebase / signing expect that suffix |
| `--gradle-task` / `--apk-glob` | No `dev` product flavor — e.g. `assembleRelease` and `app/build/outputs/apk/release/*.apk` |

After `expo prebuild`, re-run bootstrap so workspace and bundle IDs match.

## Fastlane and Ruby (Bundler)

**`Gemfile` and `Gemfile.lock`** at the **repository root** are **required** for the default **`rn.yml`** iOS jobs: each run starts with **`bundle install`**, then **`bundle exec pod install`**. **`expo prebuild` does not create these files.** Copy them from this template when missing (see [`SETUP_RN_DEVOPS_KIT.md`](../SETUP_RN_DEVOPS_KIT.md)) or use the same files shipped in **`ct-react-native-template`**’s **`ExpoTemplate`**. Align the lockfile’s **`RUBY VERSION`** with the Ruby version in **`ruby/setup-ruby`** in the iOS workflows (commonly **3.2**) if Bundler reports a mismatch.

**`fastlane/`** (at minimum **`fastlane/Fastfile`**) is **required** for default iOS jobs that run **`bundle exec fastlane staging_build`**. **`expo prebuild` does not create it.** Copy **`Fastfile`** from this repository when applying the kit (see [`SETUP_RN_DEVOPS_KIT.md`](../SETUP_RN_DEVOPS_KIT.md)); it is **not** duplicated in **`ct-react-native-template`** **`ExpoTemplate`** by design. After **`ios/`** exists in the target app, run **`bootstrap_rn_workflow_ids.py`** so workspace, Xcode project, and IPA paths in **`Fastfile`** and workflows match the app. If you maintain custom lanes, merge carefully with your bundle ID and scheme; do not overwrite your entire `app.json` / `eas.json` blindly.

## Branch names

[`rn.yml`](../.github/workflows/rn.yml) runs on **`main`**, **`master`**, and **`development`**. Adjust the `on.push` / `on.pull_request` branches if your integration branch differs.

## Secrets

Run `python3 .github/scripts/list_workflow_secrets.py --write GITHUB_SECRETS_CHECKLIST.md` after copying workflows. Add values in **GitHub → Settings → Secrets and variables → Actions**. Never commit secret material. **`rn.yml`** does **not** use **`EXPO_TOKEN`** for Expo apps (runner-only builds). **`EXPO_TOKEN`** is still required by **other** workflows that call EAS (see the generated checklist). Regenerate the checklist after changing workflows.

## Further reading

- [`CURSOR_RN_DEVOPS_REUSE.md`](../CURSOR_RN_DEVOPS_REUSE.md) — short manifest / index  
- [`.cursor/rules/github-actions-rn-ci.mdc`](../.cursor/rules/github-actions-rn-ci.mdc) — workflow map  
- [`CURSOR_RN_DEVOPS_BOOTSTRAP_PROMPT.txt`](../CURSOR_RN_DEVOPS_BOOTSTRAP_PROMPT.txt) — manual substitution checklist if you skip the bootstrap script  
