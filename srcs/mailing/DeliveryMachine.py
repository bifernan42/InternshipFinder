import base64
import os.path
import mimetypes
from utils.helpers import get_file_content, load_json_data
from email.message import EmailMessage
from typing import Any, Dict, List, Tuple
import google.auth
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger

class DeliveryMachine:

    creds: Any
    service: Any
    flow: Any
    client_id: str
    client_secret: str
    auth_uri: str
    token_uri: str
    gmail_base_uri: str
    email_template: str
    scopes: List[str]
    sender: str

    def __init__(self, config: Dict):

        self.scopes = load_json_data(config["DM_GMAIL_SCOPES"])["SCOPES"]
        self.set_credentials(config)
        self.client_id = config["DM_CLIENT_ID"]
        self.client_secret = config["DM_CLIENT_SECRET"]
        self.sender = config["DM_SENDER"]
        self.auth_uri = config["DM_AUTH_URI"]
        self.token_uri = config["DM_TOKEN_URI"]
        self.gmail_base_uri = config["DM_GMAIL_BASE_URI"]
        self.service = build("gmail", "v1", credentials=self.creds)
        self.email_template = config["DM_EMAIL_TEMPLATE"]
        self.label_name = config["DM_LABEL_NAME"]
        self.label_id = self.get_or_create_label(self.label_name)

    def set_credentials(self, config: Dict) -> None:

        self.creds = None
        token_file = config["DM_TOKENS"]
        creds_file = config["DM_CREDENTIALS"]

        if os.path.exists(token_file):
            self.creds = Credentials.from_authorized_user_file(token_file, self.scopes)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    creds_file, self.scopes
                )
                self.creds = self.flow.run_local_server(port=0)
            with open(token_file, "w") as token:
                token.write(self.creds.to_json())

    def send_email(self, message: EmailMessage) -> Dict:

        if message is not None:
            try:
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                create_message = {"raw": encoded_message}
                send_message = (
                    self.service.users()
                    .messages()
                    .send(userId="me", body=create_message)
                    .execute()
                )

                if self.label_id:
                    self.service.users().messages().modify(
                        userId="me",
                        id=send_message["id"],
                        body={"addLabelIds": [self.label_id]}
                    ).execute()

            except HttpError as e:
                logger.error(f"Couldn't send mail: {e}")
                send_message = None
        return send_message

    def create_email(self, offer: Tuple, attachment=None) -> EmailMessage:

        if offer is not None:
            try:
                lang = "en" if offer[15] != "fr" else "fr"
                email = EmailMessage()
                email["To"] = offer[6]
                email["From"] = self.sender
                email["Subject"] = f"RE: {offer[1]}"
                email.set_content(
                    "Application"
                )
                email.add_alternative(get_file_content(self.email_template.replace("xx", lang)), subtype = 'html')
                if attachment is not None:
                    type_subtype, _ = mimetypes.guess_type(attachment.replace("xx", lang))
                    maintype, subtype = type_subtype.split("/")
                    with open(attachment.replace("xx", lang), "rb") as fp:
                        attachment_data = fp.read()
                        email.add_attachment(attachment_data, maintype, subtype)
            except Exception as e:
                logger.error(f"Couldn't create email: {e}")
                email = None
        return email

    def create_draft(self, message: EmailMessage) -> Dict:

        if message is not None:
                try:
                   encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                   create_message = {"message": {"raw": encoded_message}}
                   draft = (
                       self.service.users()
                       .drafts()
                       .create(userId="me", body=create_message)
                       .execute()
                   )
                   if self.label_id:
                       self.service.users().messages().modify(
                           userId="me",
                           id=draft["message"]["id"],
                           body={"addLabelIds": [self.label_id]}
                       ).execute()
                except HttpError as error:
                    logger.error(f"Couldn't create draft: {error}")
                    draft = None
        return draft

    def get_label_id(self, label_name: str) -> str:

       labels = self.service.users().labels().list(userId="me").execute().get("labels", [])
       for label in labels:
           if label["name"].lower() == label_name.lower():
               return label["id"]
       return None

    def get_or_create_label(self, label_name: str) -> str:

        label_id = self.get_label_id(label_name)
        if label_id:
            return label_id
        label_config = {
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        }
        created_label = self.service.users().labels().create(userId="me", body=label_config).execute()
        return created_label["id"]
