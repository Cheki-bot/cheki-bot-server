import io
import os

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from src.settings import Settings

settings = Settings(_env_file=".env")

FOLDER = "base_file"


def download_data():
    service = build("drive", "v3", developerKey=settings.google.api_key)
    query = f"'{settings.google.folder_id}' in parents"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    for file in filter(
        lambda f: f.get("name", "") == settings.google.data_filename, files
    ):
        file_id = file.get("id")
        if not file_id:
            continue
        if not os.path.exists(FOLDER):
            os.mkdir(FOLDER)
        fh = io.FileIO(f"{FOLDER}/{settings.google.data_filename}", 'w')
        request = service.files().get_media(fileId=file_id)

        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Descarga {int(status.progress() * 100)}% completada.")

    print("archivos descargados correctamente")
