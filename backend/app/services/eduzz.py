"""Eduzz API integration service — OAuth2 + MyEduzz v1 API."""

import urllib.parse
from datetime import date, datetime

import requests

from app.config import EDUZZ_API_URL, EDUZZ_CLIENT_ID, EDUZZ_CLIENT_SECRET, EDUZZ_REDIRECT_URI

EDUZZ_AUTH_URL = "https://accounts.eduzz.com/oauth/authorize"
EDUZZ_TOKEN_URL = "https://accounts-api.eduzz.com/oauth/token"


# ---------------------------------------------------------------------------
# OAuth2 helpers
# ---------------------------------------------------------------------------

def get_auth_url(account_id: int) -> str:
    """Return the Eduzz OAuth2 authorization URL for a specific account."""
    params = {
        "client_id": EDUZZ_CLIENT_ID,
        "responseType": "code",
        "redirectTo": EDUZZ_REDIRECT_URI,
        "state": str(account_id),
    }
    return EDUZZ_AUTH_URL + "?" + urllib.parse.urlencode(params)


def exchange_code(code: str, account_id: int) -> dict:
    """Exchange an OAuth2 authorization code for an access token and save to DB."""
    try:
        resp = requests.post(
            EDUZZ_TOKEN_URL,
            headers={"accept": "application/json"},
            json={
                "client_id": EDUZZ_CLIENT_ID,
                "client_secret": EDUZZ_CLIENT_SECRET,
                "code": code,
                "redirect_uri": EDUZZ_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return {"error": f"Falha ao obter token: {exc}"}

    access_token = data.get("access_token")
    if not access_token:
        return {"error": f"Token não retornado: {data}"}

    user = data.get("user", {})

    from app.database import get_session, EduzzAccount
    with get_session() as session:
        account = session.get(EduzzAccount, account_id)
        if not account:
            return {"error": "Conta não encontrada."}
        account.access_token = access_token
        account.eduzz_user_id = str(user.get("eduzzId", ""))
        if not account.email and user.get("email"):
            account.email = user["email"]
        if not account.name or account.name == "Nova conta":
            account.name = user.get("name", account.name)

    return {"ok": True, "name": user.get("name", ""), "email": user.get("email", "")}


def _headers(account_id: int) -> dict | None:
    """Return bearer auth headers for an account, or None if not connected."""
    from app.database import get_session, EduzzAccount
    with get_session() as session:
        account = session.get(EduzzAccount, account_id)
        if not account or not account.access_token:
            return None
        return {
            "accept": "application/json",
            "authorization": f"bearer {account.access_token}",
        }


# ---------------------------------------------------------------------------
# Sales sync
# ---------------------------------------------------------------------------

def sync_sales(account_id: int, start_date: date, end_date: date) -> dict:
    """Fetch paid sales from Eduzz API and upsert into DB (with pagination)."""
    headers = _headers(account_id)
    if headers is None:
        return {"error": "Conta não conectada ao Eduzz. Faça a autenticação primeiro."}

    created = 0
    skipped = 0
    page = 1
    total_pages = 1

    from app.database import get_session, EduzzAccount, Product, Sale

    while page <= total_pages:
        try:
            resp = requests.get(
                f"{EDUZZ_API_URL}/myeduzz/v1/sales",
                headers=headers,
                params={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "status": "paid",
                    "page": page,
                    "itemsPerPage": 100,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            # Capturar resposta de erro para debugar se for possível
            err_details = exc
            if hasattr(exc, "response") and exc.response is not None:
                err_details = f"{exc} | {exc.response.text}"
            return {"error": f"Erro na API Eduzz (página {page}): {err_details}", "created": created, "skipped": skipped}

        total_pages = data.get("pages", 1)
        items = data.get("items", [])

        with get_session() as session:
            for s in items:
                ext_id = str(s.get("id", ""))

                # Dedup by external_id
                existing = session.query(Sale).filter_by(external_id=ext_id).first()

                # Auto-upsert product from sale data
                prod_data = s.get("product", {})
                eduzz_prod_id = str(prod_data.get("id", ""))

                product = session.query(Product).filter_by(
                    account_id=account_id,
                    product_id_eduzz=eduzz_prod_id,
                ).first()

                if not product and eduzz_prod_id:
                    product = Product(
                        account_id=account_id,
                        product_id_eduzz=eduzz_prod_id,
                        name=prod_data.get("name", "Produto desconhecido"),
                        price=float((s.get("total") or {}).get("value", 0)),
                        commission_percent=0,
                    )
                    session.add(product)
                    session.flush()

                if not product:
                    skipped += 1
                    continue

                # Determine sale date (paidAt > dueDate > createdAt)
                sale_dt_str = s.get("paidAt") or s.get("dueDate") or s.get("createdAt")
                try:
                    sale_date = datetime.fromisoformat(
                        sale_dt_str.replace("Z", "+00:00")
                    ).date() if sale_dt_str else date.today()
                except (ValueError, AttributeError):
                    sale_date = date.today()

                net_gain = float((s.get("netGain") or {}).get("value", 0))

                MY_EMAIL = "sh.brunooliveira@gmail.com"

                # user_gain = minha parte (coprodutor, parceiro, afiliado ou produtor principal)
                user_gain = 0.0
                is_user_gain = False

                # Coprodutor / parceiro
                for ptn in s.get("partners") or []:
                    if isinstance(ptn, dict) and ptn.get("email") == MY_EMAIL:
                        user_gain += float((ptn.get("netGain") or {}).get("value", 0))
                        is_user_gain = True

                # Afiliado
                for aff in s.get("affiliates") or []:
                    if isinstance(aff, dict) and aff.get("email") == MY_EMAIL:
                        user_gain += float((aff.get("netGain") or {}).get("value", 0))
                        is_user_gain = True

                # Recebedor direto (produtor principal da venda)
                recipient = s.get("recipient") or {}
                if not is_user_gain and recipient.get("email") == MY_EMAIL:
                    user_gain = net_gain
                    is_user_gain = True

                # Fallback: se nenhuma identificação bateu, assume produtor principal
                if not is_user_gain:
                    user_gain = net_gain
                
                # Update existing or add new
                if existing:
                    existing.value = net_gain
                    existing.commission_value = user_gain
                    existing.date = sale_date
                    skipped += 1
                    continue

                session.add(Sale(
                    product_id=product.id,
                    date=sale_date,
                    value=net_gain,          # Produção total (Produtor)
                    commission_value=user_gain, # Minha parte (Coprodutor / Produtor)
                    quantity=1,
                    source="eduzz_api",
                    external_id=ext_id,
                ))
                created += 1

        page += 1

    return {"created": created, "skipped": skipped}


def get_summary(account_id: int, start_date: date, end_date: date) -> dict | None:
    """Fetch the sales summary directly from Eduzz API."""
    headers = _headers(account_id)
    if headers is None:
        return None
    try:
        resp = requests.get(
            f"{EDUZZ_API_URL}/myeduzz/v1/sales/summary",
            headers=headers,
            params={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "status": "paid",
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None
