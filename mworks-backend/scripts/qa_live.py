#!/usr/bin/env python3
"""Live QA harness against the Compose API. Not imported by pytest."""
from __future__ import annotations

import json
import sys
import uuid
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
results: list[tuple[bool, str, str]] = []


def req(method: str, path: str, body=None, headers=None, timeout: int = 8, raw: bytes | None = None):
    h = {"Accept": "application/json"}
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            blob = resp.read()
            parsed = json.loads(blob) if blob else None
            return resp.status, dict(resp.headers), parsed
    except urllib.error.HTTPError as e:
        blob = e.read()
        try:
            parsed = json.loads(blob) if blob else None
        except Exception:
            parsed = blob.decode("utf-8", "replace")
        return e.code, dict(e.headers), parsed
    except Exception as e:
        return 0, {}, {"error": str(e)}


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((ok, name, detail))
    print(("PASS" if ok else "FAIL") + f"  {name}" + (f"  | {detail}" if detail else ""), flush=True)


def main() -> int:
    st, hdr, body = req("GET", "/health")
    check("GET /health 200", st == 200 and isinstance(body, dict) and body.get("status") == "ok", f"{st} {body}")
    check("no Server header", "Server" not in hdr and "server" not in hdr)
    check("nosniff + DENY + no-store", hdr.get("X-Content-Type-Options") == "nosniff" and hdr.get("X-Frame-Options") == "DENY" and "no-store" in (hdr.get("Cache-Control") or ""))

    st, _, body = req("GET", "/ready")
    check("GET /ready", st == 200 and isinstance(body, dict) and body.get("database") == "ok", f"{st} {body}")

    st, _, body = req("TRACE", "/health")
    check("TRACE blocked", st in (405, 400), f"{st} {body}")

    st, _, body = req("GET", "/v1/listings/invoice-bot")
    check("listing by slug", st == 200 and isinstance(body, dict) and body.get("id") == "invoice-bot")

    st, _, body = req("GET", "/v1/listings/" + "0" * 32)
    check("unknown listing 404", st == 404)

    st, _, body = req("GET", "/v1/listings?type=document")
    check("type=document", st == 200 and isinstance(body, list) and len(body) == 2 and all(x["type"] == "document" for x in body), f"n={len(body) if isinstance(body, list) else body}")

    st, _, body = req("GET", "/v1/listings?q=invoice")
    check("q=invoice", st == 200 and isinstance(body, list) and any(x["id"] == "invoice-bot" for x in body))

    st, _, body = req("POST", "/v1/auth/login", {"email": "henry@mworks.ng", "password": "wrong"})
    check("bad password 401", st == 401 and isinstance(body, dict) and body.get("code") == "AUTH_FAILED")

    st, _, nobody = req("POST", "/v1/auth/login", {"email": "nobody@mworks.ng", "password": "ChangeMe1a!"})
    st2, _, wrong = req("POST", "/v1/auth/login", {"email": "henry@mworks.ng", "password": "nopeNope1"})
    check("unknown vs wrong password same body", nobody == wrong, f"{nobody} vs {wrong}")

    st, _, body = req("POST", "/v1/auth/signup", {"name": "X", "email": "x@mworks.ng", "password": "Strong9x", "is_admin": True})
    check("signup extra is_admin 422", st == 422)

    st, _, henry = req("POST", "/v1/auth/login", {"email": "henry@mworks.ng", "password": "ChangeMe1a!"})
    check("demo login", st == 200 and isinstance(henry, dict) and "access_token" in henry)
    h_auth = {"Authorization": f"Bearer {henry.get('access_token', '')}"}

    token = henry.get("access_token", "")
    parts = token.split(".")
    check("JWT three segments", len(parts) == 3)
    if len(parts) == 3:
        import base64

        pad = "=" * (-len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + pad))
        pad = "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        check("JWT alg RS256", header.get("alg") == "RS256", str(header))
        check("JWT exp iss aud", all(k in claims for k in ("exp", "iss", "aud")))

    st, _, body = req("GET", "/v1/orders")
    check("orders unauth 401", st == 401)
    st, _, body = req("POST", "/v1/listings/invoice-bot/checkout", {"kind": "purchase"})
    check("checkout unauth 401", st == 401)

    st, _, body = req("POST", "/v1/listings/invoice-bot/checkout", {"kind": "purchase"}, h_auth)
    check("cannot buy own listing", st == 400, f"{st} {body}")

    st, _, body = req("POST", "/v1/listings/invoice-bot/checkout", {"kind": "hire", "budget": 10000}, h_auth)
    check("hire without brief 400", st in (400, 422), f"{st} {body}")

    st, _, body = req(
        "POST",
        "/v1/listings/invoice-bot/checkout",
        {"kind": "revise", "brief": "Please revise this automation for payroll close.", "budget": 10000},
        h_auth,
    )
    check("revise on automation 400", st == 400, f"{st} {body}")

    email = f"qa-{uuid.uuid4().hex[:8]}@mworks.ng"
    st, _, buyer = req("POST", "/v1/auth/signup", {"name": "QA Buyer", "email": email, "password": "BuyerPass9x", "role": "buyer"})
    check("signup buyer", st == 201, f"{st}")
    b_auth = {"Authorization": f"Bearer {buyer.get('access_token', '')}"}

    st, _, body = req(
        "POST",
        "/v1/listings",
        {
            "type": "document",
            "title": "Should not create as buyer",
            "blurb": "Buyer should be forbidden from listing.",
            "description": "This listing should never be created because the user role is buyer only.",
            "category": "UAT",
            "price_value": 5000,
        },
        b_auth,
    )
    check("buyer create listing 403", st == 403)

    st, _, body = req("POST", "/v1/listings/rpa-opportunity-canvas/checkout", {"kind": "purchase"}, b_auth)
    check("purchase document", st == 201 and isinstance(body, dict) and body.get("state") == "funds_held", f"{st} {body}")
    order_id = body.get("id") if isinstance(body, dict) else None
    check("order public ref", bool(order_id) and str(order_id).startswith("MW-") and len(str(order_id)) < 20, str(order_id))

    st, _, body = req("GET", "/v1/orders", headers=b_auth)
    check("buyer sees order", st == 200 and isinstance(body, list) and any(o.get("id") == order_id for o in body))

    st, _, body = req("GET", "/v1/orders", headers=h_auth)
    check("seller GET /orders is buyer-scoped", st == 200 and isinstance(body, list) and not any(o.get("id") == order_id for o in body))

    st, _, body = req(
        "POST",
        "/v1/listings/invoice-bot/checkout",
        {"kind": "hire", "brief": "Need bank-statement mapping for a 3-entity group close.", "budget": 200000},
        b_auth,
    )
    check("hire checkout", st == 201 and isinstance(body, dict) and body.get("amount") == 200000, f"{st} {body}")

    st, _, body = req(
        "POST",
        "/v1/listings/c4-architecture-pack/checkout",
        {"kind": "revise", "brief": "Retarget C4 views to a payments core banking context.", "budget": 25000},
        b_auth,
    )
    check("revise at cap", st == 201 and isinstance(body, dict) and body.get("amount") == 25000)

    st, _, body = req(
        "POST",
        "/v1/listings/c4-architecture-pack/checkout",
        {"kind": "revise", "brief": "Over cap should fail.", "budget": 25001},
        b_auth,
    )
    check("revise over cap", st == 400)

    st, _, body = req(
        "POST",
        "/v1/listings",
        {
            "type": "document",
            "title": "QA hidden UAT pack",
            "blurb": "Should stay in review and not appear publicly.",
            "description": "A UAT pack created during QA to confirm in_review listings are not public.",
            "category": "UAT",
            "price_value": 9000,
            "license": "template",
        },
        h_auth,
    )
    check("seller create listing", st == 201)
    new_slug = body.get("id") if isinstance(body, dict) else None
    st, _, catalog = req("GET", "/v1/listings")
    ids = [x["id"] for x in catalog] if isinstance(catalog, list) else []
    check("in_review not public", new_slug not in ids, str(new_slug))
    st, _, body = req("GET", f"/v1/listings/{new_slug}")
    check("in_review GET 404", st == 404)

    st, _, body = req(
        "POST",
        "/v1/listings",
        {
            "type": "document",
            "title": "QA status override pack",
            "blurb": "Trying to force live status via extra field.",
            "description": "Mass assignment test for status and verified flags on listing create.",
            "category": "UAT",
            "price_value": 8000,
            "status": "live",
            "verified": True,
        },
        h_auth,
    )
    check("listing extra fields 422", st == 422)

    st, _, rotated = req("POST", "/v1/auth/refresh", {"refresh_token": buyer.get("refresh_token")})
    check("refresh rotates", st == 200 and isinstance(rotated, dict) and rotated.get("access_token") != buyer.get("access_token"))
    st, _, body = req("POST", "/v1/auth/refresh", {"refresh_token": buyer.get("refresh_token")})
    check("old refresh revoked", st == 401)

    st, _, body = req("POST", "/v1/auth/login", raw=b"{not-json", headers={"Content-Type": "application/json"})
    check("malformed JSON", st in (400, 422), f"{st} {body}")

    st, hdr, _ = req("GET", "/v1/listings", headers={"Origin": "http://localhost:5173"})
    check("CORS 5173", hdr.get("Access-Control-Allow-Origin") == "http://localhost:5173", str(hdr.get("Access-Control-Allow-Origin")))
    st, hdr, _ = req("GET", "/v1/listings", headers={"Origin": "http://evil.example"})
    check("CORS deny evil", not hdr.get("Access-Control-Allow-Origin"), str(hdr.get("Access-Control-Allow-Origin")))

    st, _, body = req("POST", "/v1/uploads/presign", {"filename": "pack.pdf", "content_type": "application/pdf", "kind": "document"})
    check("presign unauth", st == 401)
    st, _, body = req("POST", "/v1/uploads/presign", {"filename": "pack.exe", "content_type": "application/octet-stream", "kind": "document"}, b_auth)
    check("presign exe rejected", st == 400, f"{st} {body}")
    st, _, body = req("POST", "/v1/uploads/presign", {"filename": "pack.pdf", "content_type": "application/pdf", "kind": "document"}, b_auth)
    check("presign pdf", st == 200 and isinstance(body, dict) and body.get("put_url"))
    put_url = body.get("put_url") if isinstance(body, dict) else ""
    check("presign host-reachable", "127.0.0.1" in put_url or "localhost" in put_url, (put_url or "").split("?")[0])

    st, _, body = req("GET", "/v1/orders", headers={"Authorization": "Bearer not-a-jwt"})
    check("garbage JWT 401", st == 401)
    st, _, body = req("GET", "/docs")
    check("docs in local", st == 200)

    print("\n==== SUMMARY ====", flush=True)
    failed = [r for r in results if not r[0]]
    print(f"{len(results) - len(failed)} passed, {len(failed)} failed, {len(results)} total", flush=True)
    for _, name, detail in failed:
        print(f"  FAIL {name}: {detail}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
