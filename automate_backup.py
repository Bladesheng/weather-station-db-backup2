import os
import sys
import sh
import shutil
import time
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def db_dump():
    """
    Dump the database into db.sql file
    """
    try:
        FILENAME = "./dump/db.sql"
        print(f"Dumping database to {FILENAME}")

        process = sh.pg_dump(
            os.getenv("DATABASE_URL"),
            file=FILENAME,
            _out=print,
            _bg=False,
        )

        print(f"Database dumped")

    except sh.ErrorReturnCode as e:
        print(e)
        sys.exit(0)


def make_archive(source_path, destination_path, zip_name):
    """
    Zip the whole source_path folder and put the zip into destination_path
    @param source_path: folder to be zipped
    @param destination_path: where to put the zip file
    @param zip_name
    """
    try:
        print("Zipping the dumped database")

        # name of the root working directory
        root_dir = os.path.dirname(source_path)

        # name of the source folder itself - without path - (the folder you are backing up)
        base_dir = os.path.basename(source_path.strip(os.sep))

        # name of the destination folder itself
        destination_folder = os.path.basename(destination_path.strip(os.sep))

        shutil.make_archive(
            f"{destination_folder}/{zip_name}",
            "zip",
            root_dir,
            base_dir
        )
        print("Database zipped")

    except FileNotFoundError as e:
        print("Error occured while zipping database. Exiting")
        sys.exit(0)


def upload_to_gdrive(filename):
    """
    Autheticate with google's oauth and upload the file to gdrive
    @param filename: name of the uploaded file
    """
    print("Authenticating with Google OAuth")

    credentials = service_account.Credentials.from_service_account_file(
        './SA_key.json',
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)

    print("Authentication was successful. Uploading file to GDrive")

    file_metadata = {
        'name': f'{filename}.zip',
        'parents': [os.getenv("GDRIVE_FOLDER_ID")]
    }

    media = MediaFileUpload(
        f'./archive/{filename}.zip',
        mimetype='application/zip',
        resumable=True
    )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, quotaBytesUsed"
    ).execute()

    print("File uploaded successfully")
    print(f"File ID: {file.get('id')}")
    print(
        f"File size: {round(int(file.get('quotaBytesUsed')) / 1000000, 2)} MB")


def controller():
    print("Starting database backup")
    os.chdir("/app")

    db_dump()

    # name of the newly created zip file
    zip_name = "backup " + datetime.now().strftime(r"%d/%m/%Y %H:%M:%S").replace('/', '-')
    make_archive(
        source_path="./dump",
        destination_path="./archive",
        zip_name=zip_name
    )

    upload_to_gdrive(zip_name)


if __name__ == "__main__":
    controller()
