
import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db


def main():
    service_json = os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"]
    database_url = os.environ["FIREBASE_DATABASE_URL"]
    path = os.environ.get("FIREBASE_PATH", "/backups")

    service_account = json.loads(service_json)

    # Show which project the credential belongs to, not the key.
    print("Credential project ID:", service_account.get("project_id"))
    print("Database URL configured:", bool(database_url))
    print("Firebase path:", path)

    app = firebase_admin.initialize_app(
        credentials.Certificate(service_account),
        {"databaseURL": database_url},
    )

    try:
        data = db.reference(path, app=app).get()
    except Exception as exc:
        # Error type only; avoid exposing sensitive response details.
        raise RuntimeError(
            f"Firebase read failed: {type(exc).__name__}"
        ) from None

    if data is None:
        raise RuntimeError(
            f"Firebase returned null at {path}. "
            "Verify the database URL and path."
        )

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Expected an object at {path}; "
            f"received {type(data).__name__}."
        )

    if not data:
        raise RuntimeError(
            f"The path {path} exists but returned an empty object."
        )

    print("Top-level records found:", len(data))

    # Inspect the shape without printing keys or private values.
    first_value = next(iter(data.values()))
    print("First record type:", type(first_value).__name__)

    if isinstance(first_value, dict):
        print("First record child count:", len(first_value))

        nested_value = next(iter(first_value.values()), None)
        if isinstance(nested_value, dict):
            print("Nested record child count:", len(nested_value))
            print(
                "Contains a 'files' field:",
                "files" in nested_value,
            )

    output = Path("data/backups.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")

    try:
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")

        with temporary.open("r", encoding="utf-8") as file:
            json.load(file)

        if temporary.stat().st_size <= 2:
            raise RuntimeError("Export unexpectedly contains no data.")

        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()

    print("Export file size:", output.stat().st_size, "bytes")
    print("Export completed successfully.")


if __name__ == "__main__":
    main()
