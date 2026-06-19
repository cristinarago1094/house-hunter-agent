"""Create the Gmail OAuth token for House Hunter Agent."""

import argparse
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CLIENT_SECRET_PATH = Path("credentials/client_secret.json")
TOKEN_PATH = Path("credentials/token.json")


def main():
    """Open the Google login flow and store a read-only Gmail token."""
    parser = argparse.ArgumentParser(description="Connect House Hunter Agent to Gmail.")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Print the Google login link instead of opening the browser.",
    )
    args = parser.parse_args()

    if not CLIENT_SECRET_PATH.exists():
        raise FileNotFoundError(
            "Missing credentials/client_secret.json. "
            "Download the OAuth Desktop app JSON from Google Cloud first."
        )

    credentials = None
    if TOKEN_PATH.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_PATH,
            SCOPES,
        )
        credentials = flow.run_local_server(
            port=0,
            open_browser=not args.manual,
        )

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Gmail token saved to {TOKEN_PATH}")


if __name__ == "__main__":
    main()
