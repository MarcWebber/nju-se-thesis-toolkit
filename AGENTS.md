# Project instructions

Keep this toolkit small and reuse maintained upstream tools instead of copying their implementations.

Do not add or restore automated test suites unless the user asks. Validate changes with syntax checks, CLI smoke checks, and scoped actual command runs.

Use real upstream services, installed applications, and actual artifacts for delivery verification. Do not use mocks. Verify the affected workflow through its user-visible result; describe the exact evidence and pending checks. Reduce verification only when the user explicitly requests quick delivery, and report what was checked.

After every repository change:

1. Run the smallest relevant validation.
2. Read `.lark-sync.yaml` and update the affected sections of the configured Lark report.
3. Keep component descriptions, validation results, and unfinished checks current. Use native numbered headings and lists where appropriate.
4. Read back the updated section before claiming synchronization succeeded.

If the document target or Lark authorization is unavailable, do not guess a target or silently skip synchronization. Report it as pending and leave the repository change intact.
