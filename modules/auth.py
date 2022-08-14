import json
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


def gmail_authenticate():
    SCOPES = ['https://mail.google.com/']
    SETTING_JSON = 'settings.json'
    creds = None

    settings = {}
    if os.path.exists(SETTING_JSON):
        with open('./settings.json', 'r') as f:
            settings = json.load(f)

    auth_path = str(settings['google_auth_path'])

    if os.path.exists(auth_path + 'token.json'):
        creds = Credentials.from_authorized_user_file(auth_path + 'token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(auth_path + 'token.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(auth_path + 'token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
