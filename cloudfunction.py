import base64
import json
import requests

METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
SERVICE_ACCOUNT = 'default'


def get_access_token():
    url = '{}instance/service-accounts/{}/token'.format(
        METADATA_URL, SERVICE_ACCOUNT)
    # Request an access token from the metadata server.
    r = requests.get(url, headers=METADATA_HEADERS)
    r.raise_for_status()

    # Extract the access token from the response.
    access_token = r.json()['access_token']

    return access_token


def hello_pubsub(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    pubsub_message_json = json.loads(pubsub_message)
    print(pubsub_message_json)
    branch_name = pubsub_message_json['source']['repoSource']['branchName']
    status = pubsub_message_json['status']
    step_terraform = pubsub_message_json['steps'][0]['name']

    if branch_name != "master" and step_terraform != "hashicorp/terraform:0.12.18" and (status == "SUCCESS" or status == "FAILURE"):
        access_token = get_access_token()
        headers = {'Authorization': 'Bearer {}'.format(access_token)}

        payload = {
            "repoName": "gke-cgi",
            "projectId": "gke-cgi",
            "branchName": branch_name
        }

        r = requests.post('https://cloudbuild.googleapis.com/v1/projects/gke-cgi/triggers/__TRIGGER_ID:run',
                          data=json.dumps(payload), headers=headers)
        print(r.text)
