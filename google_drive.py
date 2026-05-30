import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive"]


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
        self.service = build("drive", "v3", credentials=credentials)
        self.root_folder_id = os.environ.get("DRIVE_ROOT_FOLDER_ID", "")

    def create_folder(self, name: str, parent_id: str = None) -> str:
        parent = parent_id or self.root_folder_id
        meta = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent],
        }
        folder = self.service.files().create(body=meta, fields="id").execute()
        return folder.get("id")

    def upload_file(self, file_path: str, file_name: str, parent_id: str) -> str:
        if file_name.endswith(".docx"):
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_name.endswith(".pdf"):
            mime = "application/pdf"
        else:
            mime = "image/jpeg"

        meta  = {"name": file_name, "parents": [parent_id]}
        media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
        f = self.service.files().create(body=meta, media_body=media, fields="id").execute()
        return f.get("id")
