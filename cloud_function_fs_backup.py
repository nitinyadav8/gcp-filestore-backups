"""
Google Cloud Filestore Backup Management

Author: Nitin Yadav

This script provides functions for creating, listing, and deleting on-demand Google Cloud Filestore backups.

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

Example On-demand backup REST API call using curl:

curl -X POST "https://your-cloud-function-url" -H "Content-Type: application/json" -d "source_instance_name=your-instance-name&source_file_share_name=your-file-share-name"

Example API call using Cloud Scheduler:

Trigger_URL: "https://your-cloud-function-url?source_instance_name=your-instance-name&source_file_share_name=your-file-share-name"

METHOD: POST

To list the backups, make a GET request with the following parameters:

- `source_instance_name`: The name of the source instance.

Example list backups REST API call using curl:

curl -X GET "https://your-cloud-function-url" -H "Content-Type: application/json" -d "source_instance_name=your-instance-name"

Example API call using Cloud Scheduler:

Trigger_URL: "https://your-cloud-function-url?source_instance_name=your-instance-name"

METHOD: GET

To delete the backups post retention, make a GET request with the following parameters:

- `retention_days`: share the retention days in numeric value.

Example delete backups REST API call using curl:

curl -X DELETE "https://your-cloud-function-url" -H "Content-Type: application/json" -d "retention_days=numeric-value"

Example API call using Cloud Scheduler:

Trigger_URL: "https://your-cloud-function-url?retention_days=numeric-value"

METHOD: DELETE


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

def list_backups(source_instance_name):
    credentials, _ = google.auth.default()
    authed_session = AuthorizedSession(credentials)

    list_backups_url = f"https://file.googleapis.com/v1/projects/{PROJECT_ID}/locations/{BACKUP_REGION}/backups"
    
    print("Making a request to " + list_backups_url)

    try:
        # Making a GET request to list backups
        r = authed_session.get(url=list_backups_url)
        r.raise_for_status()  # Raise an HTTP Error for bad responses (4xx and 5xx)
        data = r.json()

        if r.status_code == requests.codes.ok:
            backups = data.get('backups', [])
            filtered_backups = [backup for backup in backups if f"{source_instance_name}-backup-" in backup.get('name', '')]
            print(f"List of backups for instance {source_instance_name}: {filtered_backups}")
            return json.dumps(filtered_backups)
        else:
            raise RuntimeError(data.get('error', 'Unknown error'))

    except requests.RequestException as e:
        print(f"Error: {e}")

def delete_old_backups(retention_days):
    credentials, _ = google.auth.default()
    authed_session = AuthorizedSession(credentials)

    list_backups_url = f"https://file.googleapis.com/v1/projects/{PROJECT_ID}/locations/{BACKUP_REGION}/backups"
    
    print("Making a request to " + list_backups_url)

    try:
        # Making a GET request to list backups
        r = authed_session.get(url=list_backups_url)
        r.raise_for_status()  # Raise an HTTP Error for bad responses (4xx and 5xx)
        data = r.json()

        if r.status_code == requests.codes.ok:
            backups = data.get('backups', [])
            now = time.time()
            retention_seconds = retention_days * 24 * 60 * 60

            for backup in backups:
                backup_name = backup.get('name', '')
                backup_time = time.mktime(time.strptime(backup['createTime'][:-4], "%Y-%m-%dT%H:%M:%S.%f"))

                if now - backup_time > retention_seconds:
                    print("Deleting " + backup_name + " in the background.")
                    delete_backup(authed_session, backup_name)
            if not backups:
                print("No backups found for deletion.")
        else:
            raise RuntimeError(data.get('error', 'Unknown error'))

    except requests.RequestException as e:
        print(f"Error: {e}")

def delete_backup(authed_session, backup_name):
    print("Deleting " + backup_name + " in the background.")
    r = authed_session.delete(f"https://file.googleapis.com/v1/{backup_name}")
    data = r.json()
    print(data)
    if r.status_code == requests.codes.ok:
        print(f"{r.status_code}: Deleting {backup_name} in the background.")
    else:
        raise RuntimeError(data['error'])

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
    elif request.method == 'GET':
        source_instance_name = request.args.get('source_instance_name')
        if source_instance_name:
            return list_backups(source_instance_name)
        else:
            return 'Missing required parameter: source_instance_name', 400
    elif request.method == 'DELETE':
        retention_days_param = request.args.get('retention_days')
        if retention_days_param is not None:
            retention_days = int(retention_days_param)
            delete_old_backups(retention_days)
            return 'Backup deletion triggered successfully.'
        else:
            return 'Missing required parameter: retention_days', 400
    else:
        return 'Unsupported HTTP method', 400
