import base64
import logging
import os
from typing import List, Optional, Dict

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailService:
    """Service wrapper for sending emails via the Gmail API."""

    def __init__(
        self, credentials_path: str = "credentials.json", token_path: str = "token.json"
    ) -> None:
        """
        Initializes the GmailService and authenticates the user.

        Args:
            credentials_path (str): Path to OAuth2 credentials JSON file.
            token_path (str): Path to saved user token file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service: Resource = self._authenticate()

    def _authenticate(self) -> Resource:
        """
        Authenticates the user and returns the Gmail API service instance.

        Returns:
            googleapiclient.discovery.Resource: Authenticated Gmail API service.
        """
        creds: Optional[Credentials] = None

        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logging.warning(f"Failed to load token: {e}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logging.info("Token refreshed.")
                except Exception as e:
                    logging.error(f"Failed to refresh token: {e}")
                    os.remove(self.token_path)
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"{self.credentials_path} not found.")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                try:
                    creds = flow.run_local_server(port=0)
                except Exception:
                    creds = flow.run_console()

                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
                os.chmod(self.token_path, 0o600)
                logging.info("New token saved.")

        try:
            service = build("gmail", "v1", credentials=creds)
            logging.info("Gmail service authenticated.")
            return service
        except Exception as e:
            logging.error(f"Failed to build Gmail service: {e}")
            raise

    def create_message(
        self,
        sender: str,
        to: str,
        subject: str,
        body: str,
        format_type: str = "html",
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Creates an email message with optional attachments.

        Args:
            sender (str): Sender's email address.
            to (str): Recipient's email address.
            subject (str): Subject of the email.
            body (str): Body content of the email.
            format_type (str): 'html' or 'plain'. Defaults to 'html'.
            attachments (List[str], optional): List of file paths to attach.

        Returns:
            dict: Raw base64url-encoded message dictionary.
        """
        if attachments:
            message = MIMEMultipart()
            message["to"] = to
            message["from"] = sender
            message["subject"] = subject

            body_part = MIMEText(body, format_type)
            message.attach(body_part)

            for filepath in attachments:
                try:
                    with open(filepath, "rb") as f:
                        part = MIMEApplication(
                            f.read(), Name=os.path.basename(filepath)
                        )
                    part["Content-Disposition"] = (
                        f'attachment; filename="{os.path.basename(filepath)}"'
                    )
                    message.attach(part)
                except Exception as e:
                    logging.error(f"Attachment error ({filepath}): {e}")
        else:
            message = MIMEText(body, format_type)
            message["to"] = to
            message["from"] = sender
            message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw}

    def send_email(
        self,
        sender: str,
        recipient: str,
        subject: str,
        body: str,
        format_type: str = "html",
        attachments: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """
        Sends an email using the Gmail API.

        Args:
            sender (str): Sender's email address.
            recipient (str): Recipient's email address.
            subject (str): Email subject.
            body (str): Email body content.
            format_type (str): Email format type, 'html' or 'plain'. Defaults to 'html'.
            attachments (List[str], optional): List of file paths to attach.

        Returns:
            dict | None: API response if successful, None otherwise.
        """
        message = self.create_message(
            sender, recipient, subject, body, format_type, attachments
        )
        try:
            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )
            logging.info(f"Email sent to {recipient}, Message ID: {result['id']}")
            return result
        except Exception as e:
            logging.error(f"Unexpected error sending email: {e}")
        return None
