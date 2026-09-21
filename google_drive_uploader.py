from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


class GoogleDriveUploader:
    SCOPES = [
        "https://www.googleapis.com/auth/drive.file"
    ]

    FOLDER_MIME_TYPE = (
        "application/vnd.google-apps.folder"
    )

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
    ):
        if credentials_file is None:
            raise ValueError(
                "credentials_file cannot be None"
            )

        if token_file is None:
            raise ValueError(
                "token_file cannot be None"
            )

        self.credentials_file = Path(
            credentials_file
        )

        self.token_file = Path(
            token_file
        )

        self.service = None

    def authenticate(self) -> None:
        credentials = None

        if self.token_file.exists():
            credentials = (
                Credentials.from_authorized_user_file(
                    self.token_file,
                    self.SCOPES,
                )
            )

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(Request())

        elif not credentials or not credentials.valid:

            if not self.credentials_file.exists():
                raise FileNotFoundError(
                    f"Could not find "
                    f"{self.credentials_file.resolve()}"
                )

            flow = (
                InstalledAppFlow
                .from_client_secrets_file(
                    self.credentials_file,
                    self.SCOPES,
                )
            )

            credentials = (
                flow.run_local_server(port=0)
            )

        self.token_file.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

        self.service = build(
            "drive",
            "v3",
            credentials=credentials,
        )

    def get_or_create_folder(
        self,
        folder_name: str,
    ) -> str:

        self._check_service()

        folder_id = self._find_folder(
            folder_name
        )

        if folder_id:
            print(
                f'Using existing Google Drive '
                f'folder: "{folder_name}"'
            )

            return folder_id

        print(
            f'Creating Google Drive folder: '
            f'"{folder_name}"'
        )

        return self._create_folder(
            folder_name
        )

    def _find_folder(
        self,
        folder_name: str,
    ) -> str | None:

        safe_name = folder_name.replace(
            "'",
            "\\'",
        )

        query = (
            f"name = '{safe_name}' "
            f"and mimeType = "
            f"'{self.FOLDER_MIME_TYPE}' "
            f"and trashed = false"
        )

        result = (
            self.service
            .files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        folders = result.get(
            "files",
            [],
        )

        if not folders:
            return None

        return folders[0]["id"]

    def _create_folder(
        self,
        folder_name: str,
    ) -> str:

        metadata = {
            "name": folder_name,
            "mimeType": self.FOLDER_MIME_TYPE,
        }

        folder = (
            self.service
            .files()
            .create(
                body=metadata,
                fields="id, name",
            )
            .execute()
        )

        return folder["id"]

    def upload_file(
        self,
        file_path: Path | str,
        folder_id: str | None = None,
    ) -> dict:

        self._check_service()

        if file_path is None:
            raise ValueError(
                "file_path is None. "
                "The backup manager did not return "
                "the ZIP path correctly."
            )

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Backup file does not exist: "
                f"{file_path.resolve()}"
            )

        metadata = {
            "name": file_path.name,
        }

        if folder_id:
            metadata["parents"] = [
                folder_id
            ]

        media = MediaFileUpload(
            str(file_path),
            mimetype="application/zip",
            resumable=True,
        )

        print(
            f"Uploading {file_path.name}..."
        )

        uploaded_file = (
            self.service
            .files()
            .create(
                body=metadata,
                media_body=media,
                fields="id, name, webViewLink",
            )
            .execute()
        )

        print(
            f"Uploaded successfully: "
            f"{uploaded_file['name']}"
        )

        return uploaded_file

    def _check_service(self) -> None:
        if self.service is None:
            raise RuntimeError(
                "Google Drive is not authenticated. "
                "Call authenticate() first."
            )