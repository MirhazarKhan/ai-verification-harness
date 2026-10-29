import os
from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class VerificationConfig:
    project_path: str = field(default_factory=lambda: os.getcwd())
    dev_server_url: str = "http://localhost:5173"
    target_selector: Optional[str] = None
    expected_text: Optional[str] = None
    expected_attribute: Optional[Dict[str, str]] = None
    max_retries: int = 3
    screenshot_on_failure: bool = True
    output_dir: str = field(default_factory=lambda: os.path.join(os.getcwd(), "verifier_output"))
    require_git_diff: bool = True
    check_console_errors: bool = True
    server_timeout_seconds: int = 10
    browser_timeout_ms: int = 8000

    def __post_init__(self):
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "screenshots"), exist_ok=True)
