
import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db


def main():
    service_account_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )
    database_url = os.environ.get("FIREBASE_DATABASE_URL")

    if not service_account_json:
        raise RuntimeError(
            "Missing FIREBASE_SERVICE_ACCOUNT_JSON secret"
        )

    if not database_url:
        raise RuntimeError(
            "Missing FIREBASE_DATABASE_URL secret"
        )

    # Authenticate using the service account stored in GitHub Secrets.
    service_account = json.loads(service_account_json)
    cred = credentials.Certificate(service_account)

    firebase_admin.initialize_app(
        cred,
        {"databaseURL": database_url},
    )

    # "/" exports the entire Realtime Database.
    # Set FIREBASE_PATH to export only a particular node.
    firebase_path = os.environ.get("FIREBASE_PATH", "/")
    firebase_path = firebase_path.strip("/")

    reference = db.reference(firebase_path or "/")
    data = reference.get()

    if data is None:
        raise RuntimeError(
            "Firebase returned no data. "
            "Check the database path and source data."
        )

    output_file = Path("data/firebase_data.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    print(f"Firebase export completed: {output_file}")
    print(f"Exported root/path: /{firebase_path}")


if __name__ == "__main__":
    main()
