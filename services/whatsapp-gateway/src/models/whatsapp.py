from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class WhatsAppProfile(BaseModel):
    name: str

class WhatsAppContact(BaseModel):
    wa_id: str
    profile: WhatsAppProfile

class WhatsAppTextMessage(BaseModel):
    body: str

class WhatsAppMediaMessage(BaseModel):
    id: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    caption: Optional[str] = None

class WhatsAppInteractiveMessage(BaseModel):
    type: str
    body: Optional[Dict[str, Any]] = None
    header: Optional[Dict[str, Any]] = None
    footer: Optional[Dict[str, Any]] = None
    action: Optional[Dict[str, Any]] = None

class WhatsAppMessage(BaseModel):
    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[WhatsAppTextMessage] = None
    image: Optional[WhatsAppMediaMessage] = None
    video: Optional[WhatsAppMediaMessage] = None
    audio: Optional[WhatsAppMediaMessage] = None
    document: Optional[WhatsAppMediaMessage] = None
    interactive: Optional[WhatsAppInteractiveMessage] = None

class WhatsAppStatus(BaseModel):
    id: str
    status: str
    timestamp: str
    recipient_id: str
    conversation: Optional[Dict[str, Any]] = None
    pricing: Optional[Dict[str, Any]] = None

class WhatsAppValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppMessage]] = None
    statuses: Optional[List[WhatsAppStatus]] = None

class WhatsAppChange(BaseModel):
    value: WhatsAppValue
    field: str

class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]

class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]

class WhatsAppOutboundMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = "text"
    text: Optional[Dict[str, str]] = None
    template: Optional[Dict[str, Any]] = None

class WebhookVerification(BaseModel):
    hub_mode: str = Field(alias="hub.mode")
    hub_verify_token: str = Field(alias="hub.verify_token")
    hub_challenge: str = Field(alias="hub.challenge")