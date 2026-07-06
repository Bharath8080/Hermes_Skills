---
name: get-current-time
description: Provides the current date and time. Load this skill and then reference `{{TIME}}` for the current timestamp.
category: system
trigger: when the user asks for the current date/time or when a query requires the current timestamp
scripts:
  - scripts/current_time.py
---

# Get Current Time

Provides accurate current date and time. When loaded, the agent has access to the current timestamp via the script output.

## Usage

The `current_time.py` script prints the current date/time in a clean format. The agent can call it whenever needed.

## Output Format

```
YYYY-MM-DD HH:MM:SS TZ
```

Example: `2026-07-04 01:09:41 IST`