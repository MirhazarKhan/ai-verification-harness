import subprocess
import os
from typing import Dict, Any, List

class GitChecker:
    def __init__(self, project_path: str):
        self.project_path = project_path

    def is_git_repo(self) -> bool:
        """Check if project path is inside a git repository."""
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return res.returncode == 0 and res.stdout.strip() == "true"

    def check_diff(self, require_changes: bool = True) -> Dict[str, Any]:
        """Verify that changes were actually made to disk via git status/diff."""
        if not self.is_git_repo():
            return {
                "success": True,
                "warning": "Project directory is not a git repository. Skipping Tier 1 git diff assertion.",
                "modified_files": [],
                "diff_summary": "No git repository found."
            }

        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )

        lines = [l.strip() for l in status_res.stdout.splitlines() if l.strip()]
        
        diff_res = subprocess.run(
            ["git", "diff", "--stat"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )

        if require_changes and not lines:
            return {
                "success": False,
                "tier": 1,
                "error": "TIER 1 FAILURE (Git/Disk Verification): No file changes detected on disk. The AI agent hallucinated task completion without modifying any files.",
                "modified_files": [],
                "diff_summary": ""
            }

        modified_files = [line.split()[-1] for line in lines]
        return {
            "success": True,
            "tier": 1,
            "modified_files": modified_files,
            "diff_summary": diff_res.stdout.strip() or f"Modified {len(modified_files)} files."
        }
