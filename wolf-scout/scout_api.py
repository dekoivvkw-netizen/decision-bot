#!/usr/bin/env python3
"""Wolf Scout API — eBay Finding API. Credenziali solo in env."""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MIN_PROFIT = float(os.getenv("SCOUT_MIN_PROFIT", "10"))
MIN_MARGIN = float(os.getenv("SCOUT_MIN_MARGIN", "15"))
FEE_PCT = float(os.getenv("SCOUT_FEE_PCT", "0.13"))
SHIP_IN = float(os.getenv("SCOUT_SHIP_IN", "5"))
SHIP_OUT = float(os.getenv("SCOUT_SHIP_OUT", "6"))
RESERVE_PCT = float(os.getenv("SCOUT_RESERVE_PCT", "0.05"))
RESALE_MULT = float(os.getenv("SCOUT_RESALE_MULT", "2.0"))

EBAY_APP_ID = os.getenv("EBAY_APP_ID", "").strip()
EBAY_GLOBAL_ID = os.getenv("EBAY_GLOBAL_ID", "EBAY-IT")
EBAY_FINDING = "https://svcs.ebay.com/services/search/FindingService/v1"

app = FastAPI(title="Wolf Scout API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class Deal(BaseModel):
    title: str
    price: float
    currency: str = "EUR"
    url: str
    image: Optional[str] = None
    condition: Optional[str] = None
    estimated_resale: float
    profit: float
    margin_pct: float
    status: str


class ScoutResponse(BaseModel):
    query: str
    min_price: float
    max_price: float
    source: str
    count: int
    deals: list[Deal]


def score_item(price: float, estimated_resale: float) -> tuple[float, float, str]:
    fees = estimated_resale * FEE_PCT
    reserve = estimated_resale * RESERVE_PCT
    total = price + SHIP_IN + fees + SHIP_OUT + reserve
    profit = estimated_resale - total
    margin = (profit / estimated_resale * 100.0) if estimated_resale > 0 else 0.0
    if profit >= MIN_PROFIT and margin >= MIN_MARGIN:
        status = "GREEN"
    elif profit >= 5 and margin >= 10:
        status = "YELLOW"
    else:
        status = "RED"
    return profit, margin, status


async def ebay_find(q: str, min_price: float, max_price: float, limit: int) -> list[dict[str, Any]]:
    if not EBAY_APP_ID:
        raise HTTPException(
            status_code=503,
            detail="EBAY_APP_ID non configurato. Crea un'app su developer.ebay.com",
        )
    params = {
        "OPERATION-NAME": "findItemsByKeywords",
        "SERVICE-VERSION": "1.13.0",
        "SECURITY-APPNAME": EBAY_APP_ID,
        "RESPONSE-DATA-FORMAT": "JSON",
        "REST-PAYLOAD": "true",
        "keywords": q,
        "paginationInput.entriesPerPage": str(min(limit, 50)),
        "paginationInput.pageNumber": "1",
        "GLOBAL-ID": EBAY_GLOBAL_ID,
        "itemFilter(0).name": "MinPrice",
        "itemFilter(0).value": str(min_price),
        "itemFilter(0).paramName": "Currency",
        "itemFilter(0).paramValue": "EUR",
        "itemFilter(1).name": "MaxPrice",
        "itemFilter(1).value": str(max_price),
        "itemFilter(1).paramName": "Currency",
        "itemFilter(1).paramValue": "EUR",
        "itemFilter(2).name": "ListingType",
        "itemFilter(2).value": "FixedPrice",
        "sortOrder": "BestMatch",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(EBAY_FINDING, params=params)
        r.raise_for_status()
        data = r.json()

    try:
        search = data["findItemsByKeywordsResponse"][0]
        if search.get("ack", [""])[0] not in ("Success", "Warning"):
            msg = search.get("errorMessage", [{}])[0]
            raise HTTPException(status_code=502, detail=f"eBay error: {msg}")
        result = search.get("searchResult", [{}])[0]
        items = result.get("item") or []
    except (KeyError, IndexError, TypeError) as e:
        raise HTTPException(status_code=502, detail=f"Risposta eBay non valida: {e}") from e

    out: list[dict[str, Any]] = []
    for it in items:
        try:
            title = it["title"][0]
            url = it["viewItemURL"][0]
            price = float(it["sellingStatus"][0]["currentPrice"][0]["__value__"])
            currency = it["sellingStatus"][0]["currentPrice"][0].get("@currencyId", "EUR")
            image = it["galleryURL"][0] if "galleryURL" in it else None
            condition = None
            if "condition" in it:
                condition = it["condition"][0].get("conditionDisplayName", [None])[0]
            out.append(
                {
                    "title": title,
                    "price": price,
                    "currency": currency,
                    "url": url,
                    "image": image,
                    "condition": condition,
                }
            )
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return out


@app.get("/health")
def health():
    return {"ok": True, "ebay_configured": bool(EBAY_APP_ID), "global_id": EBAY_GLOBAL_ID}


@app.get("/api/scout", response_model=ScoutResponse)
async def scout(
    q: str = Query(..., min_length=2),
    min: float = Query(0, ge=0, alias="min"),
    max: float = Query(9999, gt=0, alias="max"),
    limit: int = Query(20, ge=1, le=50),
    resale_mult: Optional[float] = Query(None),
):
    if max < min:
        raise HTTPException(status_code=400, detail="max deve essere >= min")
    mult = resale_mult if resale_mult and resale_mult > 0 else RESALE_MULT
    raw = await ebay_find(q, min, max, limit)
    deals: list[Deal] = []
    for it in raw:
        price = it["price"]
        estimated = round(price * mult, 2)
        profit, margin, status = score_item(price, estimated)
        if status == "RED":
            continue
        deals.append(
            Deal(
                title=it["title"],
                price=price,
                currency=it.get("currency") or "EUR",
                url=it["url"],
                image=it.get("image"),
                condition=it.get("condition"),
                estimated_resale=estimated,
                profit=round(profit, 2),
                margin_pct=round(margin, 1),
                status=status,
            )
        )
    deals.sort(key=lambda d: d.profit, reverse=True)
    return ScoutResponse(
        query=q,
        min_price=min,
        max_price=max,
        source="ebay-finding",
        count=len(deals),
        deals=deals,
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SCOUT_HOST", "0.0.0.0")
    port = int(os.getenv("SCOUT_PORT", "8787"))
    uvicorn.run("scout_api:app", host=host, port=port, reload=False)
