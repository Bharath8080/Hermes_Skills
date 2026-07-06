#!/usr/bin/env python3
"""Print the current date and time in a clean format."""

from datetime import datetime, timezone, timedelta
import time

# Get current local time
now = datetime.now()

# Get timezone offset
tz = time.tzname[0] if time.daylight == 0 else time.tzname[1]
offset = time.timezone
if time.daylight and time.localtime().tm_isdst:
    offset = time.altzone

# Format
print(now.strftime(f"%Y-%m-%d %H:%M:%S {tz}"))