from typing import Dict, Any
from config import VerificationConfig
from verifier.git_checker import GitChecker
from verifier.server_checker import ServerChecker
from verifier.browser_checker import BrowserChecker

class VerificationPipeline:
    def __init__(self, config: VerificationConfig):
        self.config = config
        self.git_checker = GitChecker(project_path=config.project_path)
        self.server_checker = ServerChecker(
            dev_server_url=config.dev_server_url,
            timeout_seconds=config.server_timeout_seconds
        )
        self.browser_checker = BrowserChecker(
            dev_server_url=config.dev_server_url,
            output_dir=config.output_dir,
            timeout_ms=config.browser_timeout_ms,
            screenshot_on_failure=config.screenshot_on_failure
        )

    def run_all(self, require_git_changes: bool = True) -> Dict[str, Any]:
        """Execute Tier 1, Tier 2, and Tier 3 verification checks in sequence."""
        report = {
            "success": False,
            "failed_tier": None,
            "errors": [],
            "details": {}
        }

        # Tier 1
        git_res = self.git_checker.check_diff(require_changes=require_git_changes and self.config.require_git_diff)
        report["details"]["tier_1_git"] = git_res
        if not git_res["success"]:
            report["failed_tier"] = 1
            report["errors"].append(git_res["error"])
            return report

        # Tier 2
        server_res = self.server_checker.check_health()
        report["details"]["tier_2_server"] = server_res
        if not server_res["success"]:
            report["failed_tier"] = 2
            report["errors"].append(server_res["error"])
            return report

        # Tier 3
        browser_res = self.browser_checker.verify_dom(
            target_selector=self.config.target_selector,
            expected_text=self.config.expected_text,
            expected_attribute=self.config.expected_attribute,
            check_console_errors=self.config.check_console_errors
        )
        report["details"]["tier_3_browser"] = browser_res
        if not browser_res["success"]:
            report["failed_tier"] = 3
            report["errors"].append(browser_res["error"])
            if browser_res.get("screenshot"):
                report["details"]["screenshot"] = browser_res["screenshot"]
            return report

        report["success"] = True
        return report
