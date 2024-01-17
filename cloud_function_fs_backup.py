"""
Google Cloud Filestore Backup Management

Author: Nitin Yadav

This script provides functions for creating on-demand Google Cloud Filestore backups.

## Source Code

The source code for this script is available on GitHub:

[Google Cloud Filestore Backups](https://github.com/nitinyadav8/gcp-filestore-backups)

## Configuration

Before using the script, make sure to set the following configurations:

**PROJECT_ID**: Enter your Google Cloud Project ID.
**SOURCE_INSTANCE_ZONE**: Provide the source instance zone.
**BACKUP_REGION**: Provide the target backup region.

## ENTRYPOINT

**Entry point**: main

## Usage

### Creating Backups

To create a backup, make a POST request with the following parameters:

- `source_instance_name`: The name of the source instance.
- `source_file_share_name`: The name of the source file share.

Example API call using curl:

```bash
curl -X POST "https://your-cloud-function-url" -H "Content-Type: application/json" -d "source_instance_name=your-instance-name&source_file_share_name=your-file-share-name"

Example API call using Cloud Scheduler:

Trigger_URL: "https://your-cloud-function-url?source_instance_name=your-instance-name&source_file_share_name=your-file-share-name"

METHOD: POST

"""

import google.auth
from google.auth.transport.requests import AuthorizedSession
import time
import requests
import json

PROJECT_ID = 'Enter your Google Cloud Project ID'
SOURCE_INSTANCE_ZONE = 'Provide the source instance zone'
BACKUP_REGION = 'Provide the target backup region'

def get_backup_id(source_instance_name):
    return f"{source_instance_name}-backup-{time.strftime('%Y%m%d-%H%M%S')}"

def create_backup(request):
    credentials, _ = google.auth.default()
    authed_session = AuthorizedSession(credentials)

    source_instance_name = request.args.get('source_instance_name')
    source_file_share_name = request.args.get('source_file_share_name')

    if not source_instance_name or not source_file_share_name:
        return 'Missing required parameters: source_instance_name and source_file_share_name', 400

    backup_id = get_backup_id(source_instance_name)

    trigger_run_url = f"https://file.googleapis.com/v1/projects/{PROJECT_ID}/locations/{BACKUP_REGION}/backups?backupId={backup_id}"
    headers = {
        'Content-Type': 'application/json'
    }
    post_data = {
        "description": f"{source_instance_name} scheduled backup",
        "source_instance": f"projects/{PROJECT_ID}/locations/{SOURCE_INSTANCE_ZONE}/instances/{source_instance_name}",
        "source_file_share": f"{source_file_share_name}"
    }

    print("Making a request to " + trigger_run_url)

    try:
        # Making a POST request to create a backup
        r = authed_session.post(url=trigger_run_url, headers=headers, json=post_data)
        r.raise_for_status()  # Raise an HTTP Error for bad responses (4xx and 5xx)
        data = r.json()
        print(data)

        if r.status_code == requests.codes.ok:
            print(f"{r.status_code}: The backup is uploading in the background.")
            return f"Backup created successfully: {backup_id}"
        else:
            raise RuntimeError(data.get('error', 'Unknown error'))

    except requests.RequestException as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500

# Entry point for the Cloud Function
def main(request):
    if request.method == 'POST':
        return create_backup(request)
    else:
        return 'Unsupported HTTP method', 400
