from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pydantic import BaseModel
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
import base64
from Backend.tools.gmail.gmail_sender import get_gmail_service
from Backend.routes.auth_routes import get_current_user_info
from Backend.core.utils import logger

router = APIRouter()


class EmailRequest(BaseModel):
    to: str
    subject: str
    message: str


class EmailResponse(BaseModel):
    status: str
    message_id: str
    sent_to: str


async def get_current_user():
    try:
        curr_user = await get_current_user_info()
        return {"id": curr_user["user_id"], "email": curr_user["email"]}
    except Exception as e:
        logger.error(f"GmailRoutes: Get user error: {str(e)}")
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/send_email")
def send_email(
    req: EmailRequest, response_model=EmailResponse, user=Depends(get_current_user)
):
    try:
        service = get_gmail_service()

        mime_message = MIMEText(req.message)
        mime_message["to"] = req.to
        mime_message["subject"] = req.subject

        raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        sent = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        return {"status": "sent", "message_id": sent["id"], "sent_to": req.to}

    except HttpError as error:
        raise HTTPException(status_code=500, detail=f"Gmail API error: {error}")
