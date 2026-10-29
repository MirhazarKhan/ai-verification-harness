import requests
from typing import Dict, Any

class ServerChecker:
    def __init__(self, dev_server_url: str, timeout_seconds: int = 10):
        self.dev_server_url = dev_server_url
        self.timeout_seconds = timeout_seconds

    def check_health(self) -> Dict[str, Any]:
        """Verify dev server responds with HTTP 200 and no build error overlay."""
        try:
            res = requests.get(self.dev_server_url, timeout=self.timeout_seconds)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "tier": 2,
                    "error": f"TIER 2 FAILURE (Dev Server Verification): Target URL {self.dev_server_url} returned HTTP {res.status_code}.",
                    "status_code": res.status_code
                }

            body_text = res.text.lower()
            error_keywords = [
                "failed to compile",
                "build error",
                "unhandled runtime error",
                "syntaxerror",
                "module not found",
                "vite-error-overlay"
            ]

            found_errors = [kw for kw in error_keywords if kw in body_text]
            if found_errors:
                return {
                    "success": False,
                    "tier": 2,
                    "error": f"TIER 2 FAILURE (Dev Server Verification): Dev server page contains active build/compiler errors matching: {found_errors}.",
                    "status_code": 200
                }

            return {
                "success": True,
                "tier": 2,
                "status_code": 200,
                "message": f"Dev server healthy at {self.dev_server_url} (HTTP 200)."
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "tier": 2,
                "error": f"TIER 2 FAILURE (Dev Server Verification): Dev server at {self.dev_server_url} is unreachable. Error: {str(e)}",
                "status_code": None
            }
