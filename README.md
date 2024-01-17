# gcp-filestore-backups

**Google Cloud Filestore Backup Management**

**Author: Nitin Yadav**

This script provides functions for creating on-demand Google Cloud Filestore backups using only a single Cloud Function to backup multiple GCP Filestore instances using API calls with help of Cloud Scheduler.


**Source Code**
The source code for this script is hosted on GitHub: https://github.com/nitinyadav8/gcp-filestore-backups


**Solution Approach**

The solution leverages Cloud Function and Cloud Scheduler to automate the process of:

● on-demand Filestore backup creation

● checking the status of the latest backup and

● discarding any old backups beyond a certain number of days **[USING SEPARETE CLOUD FUNCTION FOR BACKUPS DELETION - CODE IS UNDER TESTING TO HAVE ALL FUNCTIONALITY WITHIN A SINGLE CLOUD FUNCTION]**


**Configuration**

Before using the script, ensure that you have configured the necessary parameters. List the configuration variables and provide instructions on how to set them. Example:

**PROJECT_ID**: Enter your Google Cloud Project ID.

**SOURCE_INSTANCE_ZONE**: Provide the source instance zone.

**BACKUP_REGION**: Provide the target backup region.


**Solution Component: Cloud Scheduler**

A Cloud Function will be created with an HTTP trigger to interact with the Google Cloud Filestore APIs. This function will facilitate the initiation of on-demand backups, retrieval of specific backup run statuses, and the removal of older backups as needed.


**Solution Component: Cloud Scheduler**

Cloud Scheduler will be leveraged to invoke Cloud Function. Cloud Scheduler Jobs will be created to schedule to do the following:

● create a new on-demand backups using the Cloud Function at a fixed schedule (e.g. once every 2 hours etc.)

● fetch the status of the last backup at a fixed schedule (This is not mandatory)

● discard older backups again at a fixed schedule once the retention is over (e.g. every 12 hours)



**Solution Implementation**

**GCP Pre-requisites**:

1. Enable the **Cloud Scheduler**, **Cloud Functions**, and **Filestore APIs**
   
3. (Optional) Enable the **Cloud Build API** should you use Cloud Build for the deployment.
   
5. Create Service Account (e.g. backupsa@$PROJECT_ID.iam.gserviceaccount.com) with the following IAM roles:
   
     **Cloud Scheduler Admin**
   
     **Cloud Functions Admin**
   
     **Cloud Filestore Editor**
   
     **Cloud Run Invoker** (if using 2nd gen Cloud Function)
   
     **Service Account User**
   
   You may restrict to the least IAM privelges as required instead the Admin and Editor priveleges.
   
7. Verify or Grant the Service Account the role of **cloudscheduler.serviceAgent** on **service-$PROJECT_NUMBER@gcp-sa-cloudscheduler.iam.gserviceaccount.com**


**Deploy Cloud Function**

The solution is verified with **Python runtime 3.10**

1. In the Google Cloud console, go to the **Cloud Functions** page.
   
  Click Create Function and configure the function as follows:
  
  **Basics**: Environment (1st gen or 2nd gen)
  
  **Function Name**: For this example, we name the function **fsbackup**.
  
  **Region**: Region should match the GCP Filestore Source Region.
  
  **Trigger**:
  
  **Trigger type**: HTTP
  
  **Authentication**: Require authentication.
  
  **Runtime, build and connection settings**: (Maximum Timeout is 540s for 1st gen and 3600s for 2nd gen)
  
  **Runtime service account**: Service Account for FS Backups created earlier (backupsa@$PROJECT_ID.iam.gserviceaccount.com)
  
  **Ingress settings**: Allow all traffic
  
  **Source code**: Inline editor (**Copy the Python code shared in cloud_function_fs_backup.py into the main.py inline editor**)
  
  **Runtime**: Python 3.10
  
  **Entry point**: main
  
   In **requirements.txt**, add the following dependencies:
   
   **google-auth==1.19.2**
   
   **requests==2.24.0**
   
   **urllib3==1.25.11**
   


**Deploy Cloud Scheduler**

Create Cloud Scheduler jobs that triggers the fsbackup function on a specified schedule:

You may create scheduler job using Google Cloud Console OR via CLI as below:

1. **Schedule a Filestore backup every 4 hours**:
gcloud scheduler jobs create http **fsbackupschedule** \
    --schedule "0 */4 * * *" \
    --http-method=POST \
    --uri=**https://your-cloud-function-url?source_instance_name=your-instance-name&source_file_share_name=your-file-share-name** \
    --oidc-service-account-email=**SERVICE ACCOUNT CREATED EARLIER**    \
    --oidc-token-audience=**https://your-cloud-function-url** \
    --oidc-token-header=**"Content-Type: application/json"**

**Note: You need to create Scheduler Job for each Filestore Instance which you want to backup.**

2. **Schedule to identify backups for deletion once retention is over every 12 hours**:
gcloud scheduler jobs create http **fsbackupdeleteschedule** \
    --schedule "0 */12 * * *" \
    --http-method=DELETE \
    --uri=**https://your-cloud-function-url?source_instance_name=your-instance-name&source_file_share_name=your-file-share-name** \
    --oidc-service-account-email=**SERVICE ACCOUNT CREATED EARLIER**    \
    --oidc-token-audience=**https://your-cloud-function-url**

**Creating Backups**

Cloud Scheduler fsbackupschedule will invoke Cloud Function to Backup GCP Filestore Instance as per schedule OR Force Run scheduler job to inoke on-demand backup.

To create an adhoc backup using CURL, make a POST request with the following parameters:

source_instance_name: The name of the source instance.
source_file_share_name: The name of the source file share.

Example API call using curl:
**curl -X POST "https://your-cloud-function-url" -H "Content-Type: application/json" -d "source_instance_name=your-instance-name&source_file_share_name=your-file-share-name"**
