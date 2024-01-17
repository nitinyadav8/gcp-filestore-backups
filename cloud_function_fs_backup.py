"""
Google Cloud Filestore Backup Management

Author: Nitin Yadav

This script provides functions for creating, listing, and deleting Google Cloud Filestore backups.
"""

import google.auth
from google.auth.transport.requests import AuthorizedSession
import time
import requests
import json

PROJECT_ID = 'NAME YOUR PROJECT HERE'
SOURCE_INSTANCE_ZONE = 'PROVIDE SOURCE INSTANCE ZONE'
SOURCE_INSTANCE_NAME = 'PROVIDE FILESTORE INSTANCE NAME'
SOURCE_FILE_SHARE_NAME = 'PROVIDE FILESHARE NAME'
BACKUP_REGION = 'ENTER TARGET BACKUP REGION'

def get_backup_id():
    return f"{SOURCE_INSTANCE_NAME}-backup-{time.strftime('%Y%m%d-%H%M%S')}"

def create_backup(request):
    credentials, _ = google.auth.default()
    authed_session = AuthorizedSession(credentials)

    trigger_run_url = f"https://file.googleapis.com/v1/projects/{PROJECT_ID}/locations/{BACKUP_REGION}/backups?backupId={get_backup_id()}"
    headers = {
        'Content-Type': 'application/json'
    }
    post_data = {
        "description": f"{SOURCE_INSTANCE_NAME} scheduled backup",
        "source_instance": f"projects/{PROJECT_ID}/locations/{SOURCE_INSTANCE_ZONE}/instances/{SOURCE_INSTANCE_NAME}",
        "source_file_share": f"{SOURCE_FILE_SHARE_NAME}"
    }

    print("Making a request to " + trigger_run_url)

    try:
        # Making a POST request to create a backup
        r = authed_session.post(url=trigger_run_url, headers=headers, json=post_data)
        r.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        data = r.json()
        print(data)

        if r.status_code == requests.codes.ok:
            print(f"{r.status_code}: The backup is uploading in the background.")
            return f"Backup created successfully: {get_backup_id()}"
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
