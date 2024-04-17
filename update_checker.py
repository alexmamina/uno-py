import json
import os
from datetime import datetime, timezone
import subprocess
command = "curl -s 'https://api.github.com/repos/alexmamina/uno-py/commits'"
response_blob = subprocess.check_output(command, shell=True)
response = json.loads(response_blob)
dates = [datetime.fromisoformat(x['commit']['author']['date']) for x in response]
sorted(dates)
latest_commit = dates[0]

file_update = datetime.fromtimestamp(os.path.getmtime("update_checker.py")).astimezone(timezone.utc)
print(f"This file was last updated on {file_update} UTC")

utc_now = datetime.now().astimezone(timezone.utc)
print(f"Now it's {utc_now}")
print(f"Latest update to the project was: {latest_commit} UTC")

if file_update < latest_commit:
    print("There's an update likely available!"
          " If you want fewer bugs, more bugs, no changes at all, or cool new features, please"
          " follow your usual update process to get new files")
else:
    print("Seems up to date")


# https://github.com/alexmamina/uno-py/archive/refs/heads/master.zip
