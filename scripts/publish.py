"""Regenerate the HTML report, commit docs/index.html, and push to GitHub Pages."""
import os, sys, subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {result.stderr or result.stdout}")
        sys.exit(1)
    return result


def main():
    print("⟳  Generating report…")
    run(f"python3.11 {os.path.join(ROOT, 'scripts', 'report.py')}")

    diff = run("git diff --stat docs/index.html", check=False)
    if not diff.stdout.strip():
        print("✓  No changes — report is already up to date.")
        return

    print("⟳  Committing and pushing…")
    run("git add docs/index.html")
    run('git commit -m "Update live report"')
    run("git push origin main")

    print("\n✓  Published → https://lgarciaaco.github.io/panini/\n")


if __name__ == "__main__":
    main()
