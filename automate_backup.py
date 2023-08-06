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

from config import FLY_API_ACCES_TOKEN, FLY_APP_NAME, FLY_DB_NAME, GCP_CREDENTIALS_DICT, GDRIVE_FOLDER_ID


def fly_db_proxy():
    """
    Proxy connection to fly.io database
    """
    print(f"Proxying connection to {FLY_APP_NAME} database")
    try:
        return sh.fly(
            "proxy",
            "5442:5432",
            app=FLY_APP_NAME,
            t=FLY_API_ACCES_TOKEN,
            _out=print,
            _bg=True  # the proxy has to run in background
        )
    except sh.ErrorReturnCode as e:
        print(e)
        sys.exit(0)


def await_proxy(proxy_connection):
    """
    Wait until proxy connection is ready, because it runs in background
    @param proxy_connection: whatever sh.fly() returns
    """
    i = 0
    while i < 30:
        try:
            sh.pg_isready(host="127.0.0.1", port=5442)

            print("Proxy connection is ready")
            return

        except sh.ErrorReturnCode as e:
            i += 1
            time.sleep(1)

    print("Could not proxy to database. Exiting")
    proxy_connection.terminate()
    sys.exit(0)


def fly_db_dump():
    """
    Dump the database into db.sql file
    """

    proxy_connection = None
    try:
        proxy_connection = fly_db_proxy()
        await_proxy(proxy_connection)

        FILENAME = "./dump/db.sql"
        print(f"Dumping database to {FILENAME}")

        process = sh.pg_dump(
            host="127.0.0.1",
            port=5442,
            username="postgres",
            file=FILENAME,
            dbname=FLY_DB_NAME,
            _out=print,
            _bg=False,
        )

        print(f"Database dumped. Terminating proxy connection")
        proxy_connection.terminate()

    except sh.ErrorReturnCode as e:
        print(e)
        if proxy_connection:
            proxy_connection.terminate()
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

    credentials = service_account.Credentials.from_service_account_info(
        GCP_CREDENTIALS_DICT,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=credentials)

    print("Authentication was successful. Uploading file to GDrive")

    file_metadata = {
        'name': f'{filename}.zip',
        'parents': [GDRIVE_FOLDER_ID]
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
    start = time.time()

    fly_db_dump()

    # name of the newly created zip file
    zip_name = "backup " + datetime.now().strftime(r"%d/%m/%Y %H:%M:%S").replace('/', '-')
    make_archive(
        source_path="./dump",
        destination_path="./archive",
        zip_name=zip_name
    )

    upload_to_gdrive(zip_name)

    end = time.time()
    print(f"Total runtime of the python script: {round(end - start, 2)} s")


if __name__ == "__main__":
    controller()
