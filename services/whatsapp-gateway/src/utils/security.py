import hmac
import hashlib
from typing import Optional

def verify_webhook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    if not signature or not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={expected_signature}"
    
    return hmac.compare_digest(expected_signature, signature)