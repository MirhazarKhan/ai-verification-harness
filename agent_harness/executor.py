from typing import Callable, Dict, Any, Optional

class BaseAgentExecutor:
    """Interface for triggering an AI agent execution step."""

    def execute(self, prompt: str, feedback_context: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

class CustomFunctionExecutor(BaseAgentExecutor):
    """Executes a custom python function representing an agent API call or CLI command."""

    def __init__(self, action_func: Callable[[str, Optional[str]], bool]):
        self.action_func = action_func

    def execute(self, prompt: str, feedback_context: Optional[str] = None) -> Dict[str, Any]:
        success = self.action_func(prompt, feedback_context)
        return {"action_taken": True, "custom_success": success}

class SimulatedAgentExecutor(BaseAgentExecutor):
    """Simulates an AI Agent for testing verification loops."""

    def __init__(self, target_file_path: str, correct_content: str):
        self.target_file_path = target_file_path
        self.correct_content = correct_content
        self.attempts_received = 0

    def execute(self, prompt: str, feedback_context: Optional[str] = None) -> Dict[str, Any]:
        self.attempts_received += 1
        
        if self.attempts_received == 1:
            print(f"[Simulated Agent] Attempt {self.attempts_received}: Claiming task completion (Hallucination)...")
            return {"status": "claimed_done_hallucinated"}

        print(f"[Simulated Agent] Attempt {self.attempts_received}: Received verification feedback! Writing correct changes...")
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.correct_content)
        return {"status": "applied_real_fix"}
