"""
Regenerate the HTML report and push it to lgarciaaco.github.io/panini/.

Usage:
  python3 scripts/publish.py
"""
import os, sys, shutil, subprocess, tempfile
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

GITHUB_PAGES_REPO = "git@github.com:lgarciaaco/lgarciaaco.github.io.git"
DEPLOY_SUBDIR = "panini"
REPORTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "reports"))


def run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {result.stderr or result.stdout}")
        sys.exit(1)
    return result.stdout.strip()


def main():
    # 1. Regenerate report
    print("⟳  Generating report…")
    run(f"python3 {os.path.join(os.path.dirname(__file__), 'report.py')}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(REPORTS_DIR, f"wc2026_{date_str}.html")
    if not os.path.exists(report_path):
        print(f"ERROR: report not found at {report_path}")
        sys.exit(1)

    # 2. Clone pages repo into a temp dir
    print("⟳  Cloning GitHub Pages repo…")
    tmpdir = tempfile.mkdtemp(prefix="gh-pages-")
    try:
        run(f"git clone {GITHUB_PAGES_REPO} .", cwd=tmpdir)

        # 3. Copy report
        deploy_dir = os.path.join(tmpdir, DEPLOY_SUBDIR)
        os.makedirs(deploy_dir, exist_ok=True)
        shutil.copy(report_path, os.path.join(deploy_dir, "index.html"))

        # 4. Commit & push
        print("⟳  Pushing…")
        run("git add panini/index.html", cwd=tmpdir)
        commit_msg = f"Update Panini WC 2026 tracker — {date_str}"
        result = run(f'git diff --cached --quiet', cwd=tmpdir, check=False)
        if result == "":
            # No changes
            diff = run("git diff --cached --stat", cwd=tmpdir)
            if not diff:
                print("✓  No changes — report is already up to date.")
                return
        run(f'git commit -m "{commit_msg}"', cwd=tmpdir)
        run("git push origin main", cwd=tmpdir)

        print(f"\n✓  Published → https://lgarciaaco.github.io/panini/\n")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
