# PC Program List Backup

This project backs up the list of programs installed on a Windows PC before
formatting or reinstalling Windows. After the format, use the saved backup to
retrieve the program list and identify the software that needs to be installed
again.

The backup is stored locally as a ZIP archive and can also be uploaded to
Google Drive, so it remains available after the computer's drive is erased.

## What it backs up

The program scans Windows uninstall registry entries and creates:

- `installed_programs.txt` - a readable list with program names, versions,
  publishers, and install locations
- `installed_programs.csv` - the same information in spreadsheet-friendly
  format
- `winget_programs.json` - a Windows Package Manager export, when `winget` is
  available

All available files are placed in a timestamped `PC_Program_Backup_*` folder
and compressed into a ZIP archive. The archive is uploaded to the
`PC Program Backups` folder in Google Drive.

> This tool records the installed program list and does not automatically
> reinstall programs or back up program data, settings, licenses, or personal
> files. Keep separate backups of anything else you need before formatting.

## Requirements

- Windows
- Python 3.10 or newer
- Google Drive API OAuth client credentials
- Optional: `winget` for the package export

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Google Drive setup

1. Create or select a project in the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the Google Drive API.
3. Create an OAuth client ID for a desktop application.
4. Download the client secrets file and save it as `credentials.json` in this
   project folder.

Do not commit or share `credentials.json` or `token.json`. They are ignored by
Git through `.gitignore`. On the first run, a browser window opens for Google
authentication; the resulting token is reused on later runs.

## Create a backup

Run this command from the project directory:

```powershell
python main.py
```

The script will:

1. Scan the installed programs on the current Windows PC.
2. Write the text, CSV, and available Winget export files.
3. Create a timestamped ZIP archive in `backups`.
4. Authenticate with Google Drive.
5. Create or reuse the `PC Program Backups` folder.
6. Upload the ZIP archive and print its local path and Drive link.

## Retrieve the list after formatting Windows

1. Open Google Drive and go to `PC Program Backups`.
2. Download the ZIP archive created before the format.
3. Extract it and open `installed_programs.txt` or
   `installed_programs.csv` to review the software list.
4. If `winget_programs.json` is present, use it as a reference for reinstalling
   packages with Windows Package Manager.

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Runs the complete local-backup and Google Drive-upload workflow |
| `backup_programs.py` | Scans installed programs and creates the backup archive |
| `google_drive_uploader.py` | Authenticates with Google Drive and uploads the ZIP |
| `requirements.txt` | Python dependencies |
| `backups/` | Local backup output (ignored by Git) |
