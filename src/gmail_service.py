"""
Gmail Service Module

This module defines the GmailService class that provides methods to authenticate
with the Gmail API and to send emails. The authentication process uses OAuth2.
If a valid token is available (token.json), it is reused; otherwise, a new token
is obtained and stored.

Scopes: https://developers.google.com/workspace/gmail/api/auth/scopes
    - https://www.googleapis.com/auth/gmail.send
    - https://www.googleapis.com/auth/gmail.readonly
    - https://www.googleapis.com/auth/gmail.modify
"""

import base64
import logging
import os
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# Configure logging
logger = logging.getLogger(__name__)

# Define the scopes for read and send operations.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailService:
    """Service wrapper for sending and reading emails via the Gmail API."""

    def __init__(
        self, credentials_path: str = "credentials.json", token_path: str = "token.json"
    ) -> None:
        """
        Initializes the GmailService instance and authenticates the user.

        Args:
            credentials_path (str): Path to the OAuth2 credentials JSON file.
            token_path (str): Path to the saved user token file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service: Resource = self._authenticate()

    def _authenticate(self) -> Resource:
        """
        Authenticates the user using OAuth2 and returns the Gmail API service instance.

        The process is as follows:
          1. Attempt to load credentials from the token file if it exists.
          2. If credentials exist but are not valid (e.g. expired), attempt to refresh them.
          3. If there are no credentials or refresh fails, start a new OAuth flow.
          4. Save the new token for subsequent use.
          5. Build and return the Gmail API service instance.

        Returns:
            Resource: An authenticated Gmail API service instance.

        Raises:
            FileNotFoundError: If the credentials file is not found.
            Exception: If building the Gmail service fails.
        """
        creds: Optional[Credentials] = None

        # Step 1. Load credentials from token file if it exists.
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                logging.info("Loaded existing token from %s.", self.token_path)
            except Exception as e:
                logging.warning("Failed to load token from %s: %s", self.token_path, e)

        # Step 2. If no valid credentials are available, attempt to refresh.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logging.info("Credentials refreshed successfully.")
                except Exception as e:
                    logging.error("Failed to refresh credentials: %s", e)
                    os.remove(self.token_path)
                    logging.info(
                        "Invalid token removed. Restarting authentication flow."
                    )
                    creds = None

            # Step 3. If there are no valid credentials, run the OAuth flow.
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_path}' not found."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(
                    port=0
                )  # Attempt to run local server flow.

                # Step 3.5 Save the newly obtained credentials.
                with open(self.token_path, "w") as token_file:
                    token_file.write(creds.to_json())
                os.chmod(self.token_path, 0o600)
                logging.info("New token obtained and saved to %s.", self.token_path)

        # Step 4. Build the Gmail API service.
        try:
            service = build("gmail", "v1", credentials=creds)
            logging.info("Gmail service built and authenticated successfully.")
            return service
        except Exception as e:
            logging.error("Failed to build Gmail service: %s", e)
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
        Creates a MIME email message with optional file attachments.

        Args:
            sender (str): The sender's email address.
            to (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The body content of the email.
            format_type (str): Format of the email content, either 'html' or 'plain'. Defaults to 'html'.
            attachments (Optional[List[str]]): List of file paths for attachments.

        Returns:
            Dict[str, str]: A dictionary containing the base64url-encoded email message.
        """
        if attachments:
            message = MIMEMultipart()
            message["to"] = to
            message["from"] = sender
            message["subject"] = subject

            # Attach the email body.
            message.attach(MIMEText(body, format_type))

            # Attach each file in the attachments list.
            for filepath in attachments:
                try:
                    with open(filepath, "rb") as file:
                        file_content = file.read()
                    part = MIMEApplication(
                        file_content, Name=os.path.basename(filepath)
                    )
                    part["Content-Disposition"] = (
                        f'attachment; filename="{os.path.basename(filepath)}"'
                    )
                    message.attach(part)

                except Exception as e:
                    logging.error("Error attaching file %s: %s", filepath, e)
        else:
            # Create a simple MIMEText message if no attachments are provided.
            message = MIMEText(body, format_type)
            message["to"] = to
            message["from"] = sender
            message["subject"] = subject

        # Encode the message as a base64url string.
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw_message}

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
        Sends an email using the authenticated Gmail API.

        Args:
            sender (str): Sender's email address.
            recipient (str): Recipient's email address.
            subject (str): Email subject.
            body (str): Email body content.
            format_type (str): Format type of the email, either 'html' or 'plain'. Defaults to 'html'.
            attachments (Optional[List[str]]): List of file paths for email attachments.

        Returns:
            Optional[Dict]: The API response if the email is sent successfully, otherwise None.
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
            logging.info(
                "Email sucessfully sent to %s; Message ID: %s", recipient, result.get("id")
            )
            return result
        except Exception as e:
            logging.error("Error sending email to %s: %s", recipient, e)
        return None


if __name__ == "__main__":
    # Example usage:
    service = GmailService(credentials_path="credentials.json", token_path="token.json")
    # Replace the following details with valid ones before running.
    sender_email = "your-email@gmail.com"
    recipient_email = "recipient@example.com"
    subject = "Test Email"
    body = "<h1>Hello from Gmail API</h1><p>This is a test message.</p>"
    # Optionally add attachments, e.g., ["path/to/file.pdf"]
    response = service.send_email(
        sender=sender_email,
        recipient=recipient_email,
        subject=subject,
        body=body,
        format_type="html",
        attachments=None,
    )
    if response:
        logging.info("Response: %s", response)
