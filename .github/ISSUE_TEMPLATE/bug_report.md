--
name: Bug report
about: Create a report to help us improve SAS
title: "[BUG] "
labels: bug
assignees: ""
---

## Describe the bug

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Send request to `POST /v1/audit`
2. Use this payload:

```json
{
  "source": "...",
  "response": "...",
  "experimental": true
}
```

3. See error.

## Expected behavior

Describe what you expected to happen.

## Actual behavior

Describe what actually happened.

## Screenshots or Logs

If applicable, add screenshots, logs, stack traces, or error messages.

```text
Paste logs here
```

## Environment

Please complete the following information:

- OS: [e.g., Windows 11, Ubuntu 22.04]
- Python version: [e.g., 3.10]
- SAS version: [e.g., 1.0]
- Deployment: [local, Docker, cloud]
- Endpoint affected: [e.g., `/v1/audit`, `/v1/diff`, `/v1/chat`]

## Additional context

Add any other context about the problem here.
