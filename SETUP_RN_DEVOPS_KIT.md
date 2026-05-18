# Apply RN DevOps kit from a template clone

From the **target app** repository root (where `package.json` and `android/` live), copy infrastructure only:

```bash
TEMPLATE_ROOT="/absolute/path/to/pipeline_rn"   # or this template repo

rsync -a --delete "${TEMPLATE_ROOT}/.github/" "./.github/"
rsync -a "${TEMPLATE_ROOT}/.semgrep/" "./.semgrep/"
rsync -a "${TEMPLATE_ROOT}/.cursor/" "./.cursor/"
```

Cursor agents should follow **[`.cursor/skills/rn-devops-apply-kit/SKILL.md`](.cursor/skills/rn-devops-apply-kit/SKILL.md)** in the target repo for ordered steps, user inputs, and token discipline (shell/scripts first).

**Root `Gemfile` / `Gemfile.lock` (Bundler):** The default **`rn.yml`** iOS jobs run **`bundle install`** at the repo root. If either file is missing, copy from the template (do not overwrite an existing **`Gemfile`** without review):

```bash
if [ ! -f ./Gemfile ] || [ ! -f ./Gemfile.lock ]; then
  cp "${TEMPLATE_ROOT}/Gemfile" "${TEMPLATE_ROOT}/Gemfile.lock" ./
fi
```

**`fastlane/` (Fastlane):** Default **`rn.yml`** iOS jobs run **`bundle exec fastlane staging_build`**. If **`./fastlane/Fastfile`** is missing, copy from the template (do not overwrite an existing **`fastlane/`** without review):

```bash
if [ ! -f ./fastlane/Fastfile ]; then
  mkdir -p fastlane
  cp "${TEMPLATE_ROOT}/fastlane/Fastfile" ./fastlane/
fi
```

Do **not** delete the app’s `src/` unless you intend to replace it. Merge custom **`fastlane/`** changes and root config (`eas.json`, `app.json`) deliberately if you already maintain forks of those files.

After copy, run bootstrap substitutions (bundle id, scheme, package name) per `CURSOR_RN_DEVOPS_BOOTSTRAP_PROMPT.txt`, or from the target repo run `python3 .github/scripts/bootstrap_rn_workflow_ids.py` (see `docs/RN_WORKFLOW_REUSE.md`).

Append any missing lines from `GITIGNORE_APPEND.txt` to `.gitignore`.

If the app lists **`expo`** in `package.json`, run **`npx expo prebuild --clean`** (correct `APP_ENV` / flavor), then **commit `android/` and `ios/`** before expecting [`rn.yml`](.github/workflows/rn.yml) native jobs to pass — see [`docs/RN_WORKFLOW_REUSE.md`](docs/RN_WORKFLOW_REUSE.md). Optional **EAS submit** flows live in other workflows (e.g. internal release), not in the default `rn.yml` orchestrator.
