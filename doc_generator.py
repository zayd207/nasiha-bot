import os
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive']

# Mime type map
MIME_TYPES = {
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.pdf':  'application/pdf',
    '.png':  'image/png',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
    '.webp': 'image/webp',
    '.gif':  'image/gif',
}


def _get_mime(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]
    return MIME_TYPES.get(ext, 'image/jpeg')


class GoogleDriveManager:
    def __init__(self):
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            creds_info = json.loads(creds_json)
        else:
            with open("credentials.json") as f:
                creds_info = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
        self.service = build('drive', 'v3', credentials=credentials)
        self.root_folder_id = os.environ.get("DRIVE_ROOT_FOLDER_ID", "")
        if not self.root_folder_id:
            raise EnvironmentError("DRIVE_ROOT_FOLDER_ID environment variable is not set!")

    def create_folder(self, name: str, parent_id: str = None) -> str:
        """Create a folder and return its ID."""
        parent = parent_id or self.root_folder_id
        meta = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent]
        }
        folder = self.service.files().create(body=meta, fields='id').execute()
        folder_id = folder.get('id')

        # Anyone with the link can view
        self.service.permissions().create(
            fileId=folder_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        logger.info(f"Created Drive folder '{name}' → {folder_id}")
        return folder_id

    def upload_file(self, file_path: str, file_name: str, parent_id: str) -> str:
        """Upload a file and return its Drive ID."""
        mime = _get_mime(file_name)
        meta  = {'name': file_name, 'parents': [parent_id]}
        media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
        result = self.service.files().create(
            body=meta, media_body=media, fields='id'
        ).execute()
        file_id = result.get('id')

        # Make file viewable by anyone with the link
        self.service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        logger.info(f"Uploaded '{file_name}' → {file_id}")
        return file_id

    def get_shareable_link(self, file_id: str) -> str:
        """Return a shareable Google Drive link for a file or folder."""
        return f"https://drive.google.com/drive/folders/{file_id}"
