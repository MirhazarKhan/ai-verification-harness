# MANDATORY AI AGENT VERIFICATION PROTOCOL

You are working in a web development repository.

## STRICT RULE: NO FALSE COMPLETION STATEMENTS

You are **STRICTLY FORBIDDEN** from declaring any task completed or telling the user "The task is done!" until you empirically verify your changes on disk and on the live dev server.

### Required Verification Command
After making file edits for any UI feature, page element, or web fix, you **MUST** run the empirical verifier script before speaking to the user:

```bash
python verify.py --selector "#your-target-element-id" --text "Expected Content"
```

### Verification Flow
1. If `python verify.py` exits with code `0`: You are authorized to report completion to the user.
2. If `python verify.py` exits with code `1`: Read the printed failure error details, fix the code on disk, and re-run `python verify.py`.
