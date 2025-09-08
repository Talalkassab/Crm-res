from fastapi import APIRouter, Request, HTTPException, Query, Body
from fastapi.responses import PlainTextResponse
import logging
import json
from src.models.whatsapp import (
    WhatsAppWebhookPayload,
    WebhookVerification
)
from src.utils.config import config
from src.utils.security import verify_webhook_signature
from src.services.queue import process_incoming_message, process_status_update

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        return PlainTextResponse(content=hub_challenge)
    else:
        logger.warning(f"Webhook verification failed: mode={hub_mode}, token_match={hub_verify_token == config.WHATSAPP_VERIFY_TOKEN}")
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("")
async def webhook_handler(
    request: Request,
    payload: WhatsAppWebhookPayload = Body(...)
):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not verify_webhook_signature(body, signature, config.WHATSAPP_WEBHOOK_SECRET):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    logger.info(f"Received webhook payload: {payload.model_dump_json()}")
    
    for entry in payload.entry:
        for change in entry.changes:
            if change.field == "messages":
                value = change.value
                
                if value.messages:
                    for message in value.messages:
                        logger.info(f"Queuing message from {message.from_}: {message.type}")
                        process_incoming_message.delay(message.model_dump())
                        
                if value.statuses:
                    for status in value.statuses:
                        logger.info(f"Queuing status update: {status.id} -> {status.status}")
                        process_status_update.delay(status.model_dump())
    
    return {"status": "received"}