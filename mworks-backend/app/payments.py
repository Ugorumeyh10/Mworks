import hashlib
import hmac
import logging

import httpx

from app.config import Settings

log = logging.getLogger("mworks")

_PAYSTACK_INIT = "https://api.paystack.co/transaction/initialize"
_PAYSTACK_VERIFY = "https://api.paystack.co/transaction/verify/"


class PaymentError(Exception):
    pass


def verify_paystack_signature(settings: Settings, raw_body: bytes, signature: str) -> bool:
    secret = (settings.PAYSTACK_SECRET_KEY or "").encode("utf-8")
    if not secret or not signature:
        return False
    digest = hmac.new(secret, raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(digest, signature)


def initialize_payment(
    settings: Settings,
    *,
    email: str,
    amount_naira: int,
    reference: str,
) -> dict:
    callback = f"{settings.APP_PUBLIC_URL.rstrip('/')}/orders/{reference}?paid=1"
    if settings.paystack_enabled():
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": email,
            "amount": int(amount_naira) * 100,
            "currency": "NGN",
            "reference": reference,
            "callback_url": callback,
            "metadata": {"order_ref": reference},
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(_PAYSTACK_INIT, json=payload, headers=headers)
        except httpx.HTTPError:
            log.exception("paystack initialize failed")
            raise PaymentError("payments unavailable") from None
        if resp.status_code >= 400:
            log.warning("paystack initialize rejected status=%s", resp.status_code)
            raise PaymentError("payments unavailable")
        data = (resp.json() or {}).get("data") or {}
        url = data.get("authorization_url")
        if not url:
            raise PaymentError("payments unavailable")
        return {"provider": "paystack", "authorization_url": url, "reference": reference}

    if not settings.local_payments_allowed():
        raise PaymentError("payments unavailable")
    return {
        "provider": "local_test",
        "authorization_url": f"{settings.APP_PUBLIC_URL.rstrip('/')}/checkout/pay/{reference}",
        "reference": reference,
    }


def verify_paystack_reference(settings: Settings, reference: str) -> bool:
    if not settings.paystack_enabled():
        return False
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    try:
        with httpx.Client(timeout=12.0) as client:
            resp = client.get(_PAYSTACK_VERIFY + reference, headers=headers)
    except httpx.HTTPError:
        log.exception("paystack verify failed")
        return False
    if resp.status_code >= 400:
        return False
    data = (resp.json() or {}).get("data") or {}
    return data.get("status") == "success" and data.get("reference") == reference
