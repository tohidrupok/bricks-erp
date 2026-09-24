import re
import sys
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Force stdout to UTF-8 at import time
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def safe_print(msg):
    """Unicode-safe print — never crashes on Bangla or any Unicode."""
    try:
        text = str(msg)
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write((text + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        else:
            print(text.encode('utf-8', errors='replace').decode('ascii', errors='replace'))
    except Exception:
        pass  # never crash inside a debug print


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)


def extract_drive_id_from_link(link: str):
    patterns = [
        r'/drive/folders/([a-zA-Z0-9_-]+)',
        r'/folders/([a-zA-Z0-9_-]+)',
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None


def is_folder_link(link: str) -> bool:
    return bool(re.search(r'/(drive/)?folders/', link))


def get_drive_file_metadata(file_id: str):
    try:
        service = get_drive_service()
        return service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, webViewLink, modifiedTime, size"
        ).execute()
    except Exception as e:
        safe_print(f"Drive metadata error: {e}")
        return None


def list_drive_folder_contents(folder_id: str):
    try:
        service = get_drive_service()
        all_files = []
        page_token = None

        while True:
            params = dict(
                q=f"'{folder_id}' in parents and trashed = false",
                pageSize=200,
                fields="nextPageToken, files(id, name, mimeType, webViewLink, modifiedTime, size)",
                orderBy="folder,name"
            )
            if page_token:
                params['pageToken'] = page_token

            results = service.files().list(**params).execute()
            batch = results.get('files', [])
            all_files.extend(batch)
            safe_print(f"DEBUG page batch: {len(batch)} items")
            page_token = results.get('nextPageToken')
            if not page_token:
                break

        files, folders = [], []
        for item in all_files:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                folders.append(item)
            else:
                files.append(item)

        safe_print(f"DEBUG total: {len(all_files)} | files: {len(files)} | folders: {len(folders)}")
        return {'files': files, 'folders': folders}

    except Exception as e:
        safe_print(f"Drive list error: {e}")
        return {'files': [], 'folders': []}


def sync_drive_to_db(drive_id: str, db_folder, is_folder: bool = False):
    from documents.models import TrackerGoogleDriveFile
    from django.utils import timezone

    synced = 0

    if is_folder:
        safe_print(f"DEBUG syncing FOLDER id={drive_id}")
        contents = list_drive_folder_contents(drive_id)
        safe_print(f"DEBUG files to sync: {len(contents['files'])}")

        for drive_file in contents['files']:
            try:
                # Ensure clean UTF-8 string — handles Bangla file names
                file_name = drive_file.get('name', 'Untitled')
                file_name = file_name.encode('utf-8', errors='replace').decode('utf-8')

                file_id   = drive_file.get('id', '')
                file_link = drive_file.get('webViewLink', '')

                safe_print(f"DEBUG saving file id={file_id}")

                obj, created = TrackerGoogleDriveFile.objects.get_or_create(
                    google_drive_id=file_id,
                    defaults={
                        'name': file_name,
                        'folder': db_folder,
                        'google_drive_link': file_link,
                        'last_synced_at': timezone.now(),
                    }
                )
                if not created:
                    obj.name             = file_name
                    obj.folder           = db_folder
                    obj.google_drive_link = file_link
                    obj.last_synced_at   = timezone.now()
                    obj.save()

                synced += 1

            except Exception as e:
                safe_print(f"DEBUG error on file: {e}")
                continue

    else:
        safe_print(f"DEBUG syncing FILE id={drive_id}")
        meta = get_drive_file_metadata(drive_id)

        if meta:
            try:
                file_name = meta.get('name', 'Untitled')
                file_name = file_name.encode('utf-8', errors='replace').decode('utf-8')
                file_link = meta.get('webViewLink', '')

                obj, created = TrackerGoogleDriveFile.objects.get_or_create(
                    google_drive_id=drive_id,
                    defaults={
                        'name': file_name,
                        'folder': db_folder,
                        'google_drive_link': file_link,
                        'last_synced_at': timezone.now(),
                    }
                )
                if not created:
                    obj.name              = file_name
                    obj.google_drive_link = file_link
                    obj.last_synced_at    = timezone.now()
                    obj.save()

                synced += 1

            except Exception as e:
                safe_print(f"DEBUG error saving file: {e}")

    safe_print(f"DEBUG sync complete — total synced: {synced}")
    return synced