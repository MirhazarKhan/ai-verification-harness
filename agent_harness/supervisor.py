import time
from typing import Dict, Any, Optional
from config import VerificationConfig
from verifier.pipeline import VerificationPipeline
from agent_harness.executor import BaseAgentExecutor

class SupervisorLoop:
    def __init__(self, config: VerificationConfig, executor: BaseAgentExecutor):
        self.config = config
        self.executor = executor
        self.pipeline = VerificationPipeline(config)

    def run(self, task_prompt: str) -> Dict[str, Any]:
        """Run supervisor loop: Execute Agent -> Verify empirically -> Retry with feedback if failed."""
        print(f"\n=======================================================")
        print(f"[SUPERVISOR] STARTING SUPERVISOR LOOP FOR TASK:")
        print(f"   Prompt: '{task_prompt}'")
        print(f"   Target URL: {self.config.dev_server_url}")
        print(f"   Target Selector: {self.config.target_selector}")
        print(f"   Expected Text: {self.config.expected_text}")
        print(f"=======================================================\n")

        feedback_context: Optional[str] = None

        for attempt in range(1, self.config.max_retries + 1):
            print(f"--- Attempt {attempt}/{self.config.max_retries} ---")
            
            exec_result = self.executor.execute(task_prompt, feedback_context)
            print(f"Agent Action executed. Status: {exec_result}")

            time.sleep(1.5)

            print(f"Running Empirical Verification Pipeline...")
            report = self.pipeline.run_all(require_git_changes=True)

            if report["success"]:
                print(f"\n[SUCCESS] VERIFICATION SUCCESSFUL! All 3 Tiers passed empirically.")
                print(f"   - Tier 1 (Git/Disk): PASSED")
                print(f"   - Tier 2 (Dev Server): PASSED")
                print(f"   - Tier 3 (Playwright DOM): PASSED")
                return {
                    "success": True,
                    "attempts": attempt,
                    "final_report": report
                }

            failed_tier = report["failed_tier"]
            raw_errors = "\n".join(report["errors"])
            safe_errors = raw_errors.encode('ascii', 'replace').decode('ascii')
            print(f"\n[FAIL] VERIFICATION FAILED at Tier {failed_tier}!")
            print(f"   Error Details: {safe_errors}")
            
            if report["details"].get("screenshot"):
                print(f"   [SCREENSHOT] Saved at: {report['details']['screenshot']}")

            feedback_context = (
                f"AUTONOMOUS VERIFIER FEEDBACK (Attempt {attempt} Failed):\n"
                f"The previous task execution was rejected by empirical checks at Tier {failed_tier}.\n"
                f"Errors:\n{raw_errors}\n"
                f"Please fix the code files on disk so that the target URL ({self.config.dev_server_url}) "
                f"renders the expected selector ({self.config.target_selector}) with text '{self.config.expected_text}'."
            )

            print(f"Passing diagnostic feedback context to agent for auto-retry...\n")

        print(f"\n[ABORTED] TASK ABORTED: Reached maximum retries ({self.config.max_retries}) without passing empirical verification.")
        return {
            "success": False,
            "attempts": self.config.max_retries,
            "final_report": report
        }
