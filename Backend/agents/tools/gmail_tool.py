import base64
import json
from typing import Type
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from tools.gmail.gmail_sender import get_gmail_service
from core.utils import logger
from email.mime.text import MIMEText


class GmailSendInput(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Subject line of the email")
    message: str = Field(description="Body text of the email")


class GmailSendTool(BaseTool):
    name: str = "send_gmail_message"
    description: str = "Sends an email using the Gmail API. Requires valid OAuth token and credentials."
    args_schema: Type[BaseModel] = GmailSendInput

    def _run(self, to: str, subject: str, message: str) -> str:
        """
        Send an email synchronously via Gmail API.
        """
        logger.info(f"GmailSendTool: Sending email to '{to}' with subject '{subject}'")
        try:
            service = get_gmail_service()

            # Create MIME message
            mime_message = MIMEText(message)
            mime_message["to"] = to
            mime_message["subject"] = subject

            # Encode message in base64
            raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()
            message_body = {"raw": raw_message}

            sent_message = (
                service.users()
                .messages()
                .send(userId="me", body=message_body)
                .execute()
            )

            logger.info(f"Email sent successfully: ID {sent_message['id']}")
            return json.dumps({"status": "success", "id": sent_message["id"]})

        except Exception as e:
            logger.error(f"GmailSendTool error: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    async def _arun(self, to: str, subject: str, message: str) -> str:
        return self._run(to, subject, message)


def create_gmail_send_tool() -> GmailSendTool:
    """
    Factory function to create a GmailSendTool instance.
    Keeps consistency with other create_*_tool() functions.
    """
    logger.info("Creating GmailSendTool")
    return GmailSendTool()
