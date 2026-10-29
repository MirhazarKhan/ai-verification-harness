import sys
import argparse
import os
from config import VerificationConfig
from verifier.pipeline import VerificationPipeline

def main():
    parser = argparse.ArgumentParser(description="Empirically verify task completion")
    parser.add_argument("--selector", required=True, help="Target CSS selector expected on DOM (e.g. '#navbar')")
    parser.add_argument("--text", help="Expected text inside target selector")
    parser.add_argument("--url", default="http://localhost:5173", help="Dev server URL")
    parser.add_argument("--no-git", action="store_true", help="Skip Tier 1 git diff requirement")

    args = parser.parse_args()

    config = VerificationConfig(
        dev_server_url=args.url,
        target_selector=args.selector,
        expected_text=args.text,
        require_git_diff=not args.no_git,
        screenshot_on_failure=True
    )

    pipeline = VerificationPipeline(config)
    report = pipeline.run_all(require_git_changes=not args.no_git)

    if report["success"]:
        print("\n[SUCCESS] EMPIRICAL VERIFICATION PASSED!")
        print("   - Tier 1 (Git/Disk): PASSED")
        print("   - Tier 2 (Dev Server): PASSED")
        print("   - Tier 3 (Playwright DOM): PASSED")
        sys.exit(0)
    else:
        print(f"\n[FAIL] VERIFICATION FAILED at Tier {report['failed_tier']}!")
        for err in report["errors"]:
            safe_err = err.encode('ascii', 'replace').decode('ascii')
            print(f"   Error: {safe_err}")
        if report["details"].get("screenshot"):
            print(f"   Failure Screenshot: {report['details']['screenshot']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
