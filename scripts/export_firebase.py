
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
    firebase_path = os.environ.get("FIREBASE_PATH", "/backups")

    if not service_account_json or not database_url:
        raise RuntimeError("Firebase secrets are missing.")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(json.loads(service_account_json)),
            {"databaseURL": database_url},
        )

    data = db.reference(firebase_path).get()

    if not isinstance(data, dict) or not data:
        raise RuntimeError(
            f"No backup records found at {firebase_path}. "
            "Existing export was not changed."
        )

    output = Path("data/backups.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")

    try:
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")

        # Validate before replacing the existing export.
        with temporary.open("r", encoding="utf-8") as file:
            json.load(file)

        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    print(f"Exported Firebase path: {firebase_path}")
    print(f"UUID records exported: {len(data)}")
    print(f"Output file size: {output.stat().st_size} bytes")


if __name__ == "__main__":
    main()
