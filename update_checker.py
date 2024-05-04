import json
import os
from datetime import datetime, timezone
import subprocess
command = "curl -s 'https://api.github.com/repos/alexmamina/uno-py/commits'"
response_blob = subprocess.check_output(command, shell=True)
response = json.loads(response_blob)
dates = [
    datetime.strptime(
        x['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)
    for x in response
]
# Python 3.11:
# dates = [datetime.fromisoformat(x['commit']['author']['date']) for x in response]
sorted(dates)
latest_commit = dates[0]

# Get the current file's last modification time - should be the last download time
file_update = datetime.fromtimestamp(os.path.getmtime("mac_scripts")).astimezone(timezone.utc)
print(f"This file was last updated on {file_update} UTC")

utc_now = datetime.now().astimezone(timezone.utc)
print(f"Now it's {utc_now}")
print(f"Latest update to the project was: {latest_commit} UTC")

if file_update < latest_commit:
    print("There's an update likely available! Trying...")
    download_command = "cd && cd Downloads && " + \
        "curl https://github.com/alexmamina/uno-py/archive/refs/heads/master.zip -L " + \
        "--output uno-py-master.zip && unzip -o uno-py-master.zip && rm uno-py-master.zip"
    subprocess.call(download_command, shell=True)
    print("Hello! I have been updated to (probably) the latest version")
else:
    print("Seems up to date")
