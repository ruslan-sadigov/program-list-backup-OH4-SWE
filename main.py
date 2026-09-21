import traceback

from backup_programs import ProgramBackupManager
from google_drive_uploader import GoogleDriveUploader


class PCBackupApplication:
    DRIVE_FOLDER_NAME = "PC Program Backups"

    def __init__(self):
        self.backup_manager = (
            ProgramBackupManager()
        )

        self.drive_uploader = (
            GoogleDriveUploader()
        )

    def run(self) -> None:
        print("=" * 60)
        print("PC PROGRAM BACKUP")
        print("=" * 60)

        try:
            # --------------------------------
            # 1. Create local backup
            # --------------------------------

            zip_path = (
                self.backup_manager
                .create_backup()
            )

            print(
                f"\nZIP PATH: {zip_path}"
            )

            if zip_path is None:
                raise RuntimeError(
                    "create_backup() returned None."
                )

            print("\n" + "=" * 60)
            print("GOOGLE DRIVE")
            print("=" * 60)

            # --------------------------------
            # 2. Authenticate
            # --------------------------------

            print(
                "Authenticating with Google..."
            )

            self.drive_uploader.authenticate()

            # --------------------------------
            # 3. Create/find Drive folder
            # --------------------------------

            folder_id = (
                self.drive_uploader
                .get_or_create_folder(
                    self.DRIVE_FOLDER_NAME
                )
            )

            # --------------------------------
            # 4. Upload ZIP
            # --------------------------------

            uploaded_file = (
                self.drive_uploader
                .upload_file(
                    zip_path,
                    folder_id,
                )
            )

            print("\n" + "=" * 60)
            print("BACKUP COMPLETE")
            print("=" * 60)

            print(
                "\nLocal ZIP:"
            )

            print(
                zip_path.resolve()
            )

            web_link = uploaded_file.get(
                "webViewLink"
            )

            if web_link:
                print(
                    "\nGoogle Drive link:"
                )

                print(
                    web_link
                )

        except Exception as error:
            print("\n" + "=" * 60)
            print("BACKUP FAILED")
            print("=" * 60)

            print(
                f"\nError: {error}"
            )

            print(
                "\nFull traceback:"
            )

            traceback.print_exc()


def main():
    application = PCBackupApplication()
    application.run()


if __name__ == "__main__":
    main()