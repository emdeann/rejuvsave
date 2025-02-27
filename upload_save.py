import shutil
import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_ID = '1qshwEt0oau4aMw0-VLxCR8lpiUexEhV4'

def save_backup():
    # Make backup folder (in cwd) if it doesn't exist
    if not os.path.isdir('Backup'):
        os.mkdir('Backup')
    
    # Copy current save to backup folder
    shutil.copy2('Game.rxdata', 'Backup')
    print('Save data sent to backups folder')

def download_latest_backup(service):
    print('Getting latest backup from Drive...')
    back = get_latest_backup(service)
    if back:
        request = service.files().get_media(fileId=back)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        
        while done is False:
            _, done = downloader.next_chunk()
        
        with open('Game.rxdata', 'wb') as f:
            f.write(file.getvalue())
        print('Latest backup downloaded!')
    else:
        print("No Drive file found!")

def get_latest_backup(service):
    q = f"'{FOLDER_ID}' in parents and name = 'Game.rxdata'"
    results = (
        service.files()
        .list(q=q, pageSize=1, fields="files(id, name)")
        .execute()
    )
    items = results.get('files', [])
    
    # If a backup exists, return it
    if items:
        return items[0]['id']

def send_backup_to_drive(service):
    # Remove old backup
    back = get_latest_backup(service)
    if back:
        service.files().delete(fileId=get_latest_backup(service)).execute()
        print('Deleted old backup from Drive')
    
    # Name and upload new backup file
    print('Starting upload...')
    metadata = {'name': 'Game.rxdata', 'parents': [FOLDER_ID]}
    media = MediaFileUpload(filename='Game.rxdata', mimetype='application/octet-stream')
    file = service.files().create(body=metadata, media_body=media, fields='id').execute()
    
    print('Save data sent to Drive!')
    
    return file.get('id')

def api_login():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    try:
        service = build("drive", "v3", credentials=creds)  
    except HttpError as error:
        print(error)
    
    print('Logged into Drive') 
    return service

def main():
    service = api_login()
    send_backup_to_drive(service)

if __name__ == "__main__":
  main()