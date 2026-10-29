# Autonomous AI Task Verification Engine 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Tested%20with-Playwright-2EAD33.svg?logo=playwright&logoColor=white)](https://playwright.dev/)
[![Status: Active](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

> **Eliminate AI Coding Agent Hallucinations with Empirical 3-Tier Verification.**  
> A standalone, lightweight verification pipeline and supervisor loop that prevents AI coding agents (Claude Code, Cursor, Windsurf, Aider, Devin, etc.) from falsely declaring task completion on web projects.

---

## 🎯 The Problem

Modern AI coding agents frequently suffer from **premature completion hallucination**:
1. **Zero-Edit Hallucination:** The agent describes fixing a bug or building a feature, but made no physical changes to the codebase.
2. **Broken Builds:** The agent edits files, but introduces syntax errors or broken imports that crash the dev server.
3. **Silent DOM / Runtime Failures:** The dev server runs, but the UI component fails to render, throws uncaught JavaScript console exceptions, or displays the wrong text.

---

## ⚡ The Solution: 3-Tier Empirical Verification

```text
       [AI Agent Claims Completion]
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │  Tier 1: Git & Disk Verification    │──► (No files changed) ──► [REJECT + FEEDBACK]
  │  Validates physical code mutations  │
  └──────────────────┬──────────────────┘
                     │ PASSED
                     ▼
  ┌─────────────────────────────────────┐
  │  Tier 2: Dev Server & Compiler Check│──► (HTTP 500 / Build error) ──► [REJECT + FEEDBACK]
  │  Ensures dev server compiles & runs │
  └──────────────────┬──────────────────┘
                     │ PASSED
                     ▼
  ┌─────────────────────────────────────┐
  │  Tier 3: Headless Playwright DOM    │──► (Missing DOM / JS errors) ──► [CAPTURE SCREENSHOT]
  │  Inspects live DOM & console errors │                                 │
  └──────────────────┬──────────────────┘                                 ▼
                     │ PASSED                                    [RETRY WITH DIAGNOSTICS]
                     ▼
     [EMPIRICAL COMPLETION CERTIFIED]
```

---

## 📁 Repository Structure

```text
ai-verification-harness/
├── config.py             # Dataclass configuration (timeouts, dev server URL, selectors)
├── requirements.txt      # Core dependencies (playwright, requests, pyyaml)
├── verify.py             # Standalone 1-line CLI verification script
├── AGENTS.md             # Strict protocol rules to drop into agent projects
├── LICENSE               # MIT License
├── README.md             # Documentation & architecture guide
├── verifier/             # 3-Tier Verification Engine
│   ├── git_checker.py    # Tier 1: Git/Disk status & diff analyzer
│   ├── server_checker.py # Tier 2: HTTP status & compiler error overlay detector
│   ├── browser_checker.py# Tier 3: Playwright DOM inspector & screenshot capturer
│   └── pipeline.py       # Sequential pipeline orchestrator
└── agent_harness/        # Supervisor Loop Engine
    ├── executor.py       # Abstract agent executor interface
    └── supervisor.py     # Outer supervisor retry loop with diagnostic feedback
```

---

## 🚀 Quickstart

### 1. Installation

```bash
git clone https://github.com/MirhazarKhan/ai-verification-harness.git
cd ai-verification-harness

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser engine
playwright install chromium
```

### 2. Standalone CLI Verification

Run the verifier directly from your terminal or pass it as a required verification step to your AI agent:

```bash
python verify.py --selector "#navbar" --text "Dashboard" --url "http://localhost:5173"
```

#### CLI Flags:
* `--selector`: **(Required)** Target CSS selector expected in the live DOM (e.g. `#submit-btn`, `.hero-title`).
* `--text`: **(Optional)** Expected text inside the selector.
* `--url`: **(Optional)** Dev server URL (Default: `http://localhost:5173`).
* `--no-git`: **(Optional)** Skip Tier 1 Git diff requirement (for non-git directories).

---

## 🤖 Drop-in Agent Protocol (`AGENTS.md`)

Copy `AGENTS.md` into the root of any web project. Coding agents reading `AGENTS.md` (or `.cursorrules` / `GEMINI.md`) will be instructed never to report completion without first passing `verify.py`:

```bash
# Example agent command execution:
python verify.py --selector "#checkout-total" --text "$99.00"
```

- **Exit Code `0`:** Empirical verification passed. The agent is authorized to declare the task complete.
- **Exit Code `1`:** Verification failed. The agent must read the error diagnostics, inspect the failure screenshot, and self-correct.

---

## 🐍 Python API & Autonomous Supervisor Loop

You can wrap any AI agent call in the autonomous `SupervisorLoop`:

```python
from config import VerificationConfig
from agent_harness.supervisor import SupervisorLoop
from agent_harness.executor import BaseAgentExecutor

class MyAgentExecutor(BaseAgentExecutor):
    def execute(self, prompt: str, feedback_context: str | None = None):
        # Trigger your LLM agent (e.g., via LangChain, AutoGen, or custom API)
        # Pass feedback_context if previous attempt failed!
        return {"action_taken": True}

config = VerificationConfig(
    dev_server_url="http://localhost:5173",
    target_selector="#product-card",
    expected_text="Wireless Headphones",
    max_retries=3,
    screenshot_on_failure=True
)

supervisor = SupervisorLoop(config=config, executor=MyAgentExecutor())
result = supervisor.run(task_prompt="Add the new Wireless Headphones product card")

if result["success"]:
    print(f"Verified in {result['attempts']} attempt(s)!")
else:
    print(f"Task aborted after {result['attempts']} attempts.")
```

---

## 🔍 Verification Tiers in Detail

### Tier 1: Git & Disk Verification (`git_checker.py`)
- Runs `git status --porcelain` and `git diff --stat`.
- Checks for tangible file mutations.
- Instantly catches when an agent hallucinates a fix without actually touching disk files.

### Tier 2: Server & Compilation Health (`server_checker.py`)
- Sends automated HTTP probes to the target dev server.
- Verifies HTTP 200 response codes.
- Scans response bodies for active compiler and bundler error overlays (*"Failed to compile"*, *Vite error overlays*, *Next.js unhandled runtime errors*).

### Tier 3: Playwright DOM & Console Inspection (`browser_checker.py`)
- Launches headless Chromium.
- Waits for hydration and verifies presence of the expected CSS selector.
- Asserts that text content or element attributes match expectations.
- Intercepts uncaught JavaScript `console.error` and `pageerror` events.
- Automatically captures and saves annotated screenshots to `verifier_output/screenshots/` upon failure.

---

## 🛠️ Configuration Options (`config.py`)

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `dev_server_url` | `str` | `"http://localhost:5173"` | URL of the live dev server |
| `target_selector` | `str` | `None` | CSS selector required to appear in the DOM |
| `expected_text` | `str` | `None` | Substring expected inside the target element |
| `require_git_diff` | `bool` | `True` | Require physical Git edits |
| `screenshot_on_failure` | `bool` | `True` | Save visual proof on failed verifications |
| `check_console_errors` | `bool` | `True` | Fail if page threw JavaScript runtime exceptions |
| `browser_timeout_ms` | `int` | `8000` | Playwright DOM wait timeout |
| `max_retries` | `int` | `3` | Supervisor loop retry budget |

---

## 🤝 Contributing

Contributions, feedback, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

## 👨‍💻 Author

**Mirhazar Khan**  
*Senior 3D & Creative Web Engineer | AI Systems & Procedural Graphics Researcher*  
- **GitHub:** [@MirhazarKhan](https://github.com/MirhazarKhan)  
- **Website:** [mirhazarkhan.com](https://mirhazarkhan.com)
