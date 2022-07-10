import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient import errors
from email.message import EmailMessage
import base64

def gmail_authenticate():
    SCOPES = ['https://mail.google.com/']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_label_list(service):
    results = service.users().labels().list(userId='me').execute()
    return results.get('labels', [])



def main():
    service = gmail_authenticate()

    # request a list of all the labels
    labellist = get_label_list(service)

    if not labellist:
        print('No labels found.')
        return
    print('Labels:')
    
    for label in labellist:
        print(label['name'])

    # request a list of all the messages
    result = service.users().messages().list(maxResults=500, userId='me').execute()
  
    messages = result.get('messages')

    if os.path.exists('result.txt'):
        os.remove('result.txt')

    f = open('result.txt', 'a', encoding="UTF-8-sig")
    last_msg_datetime = None
  

    while(1):
        if last_msg_datetime is None:
            query = "before: {0} after: {1}".format(today.strftime('%Y/%m/%d'),
                                            yesterday.strftime('%Y/%m/%d'))
        # iterate through all the messages
        for idx, msg in enumerate(messages):
            # Get the message from its id
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
    
            # Use try-except to avoid any Errors
            try:
                # Get value of 'payload' from dictionary 'txt'
                payload = txt['payload']
                labels = txt['labelIds']
                headers = payload['headers']
    
                # Look for Subject and Sender Email in the headers
                for d in headers:
                    if d['name'] == 'Subject':
                        subject = d['value']
                    if d['name'] == 'From':
                        sender = d['value']
                
                # check label name
                labelnames = []
            
                for l in labels:
                    for label in labellist:
                        if label['id'] == l:
                            labelnames.append(label['name'])
                            break
    
                # Printing the subject, sender's email and message
                text = f'[{idx}] DateTime: {subject}, From: {sender}, Labels:{labelnames}\n'
                print(text)
                f.write(text)

            except:
                f.close()
                pass
   
    f.close()

if __name__ == '__main__':
    main()