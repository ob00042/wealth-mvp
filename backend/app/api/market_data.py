from datetime import date, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from app.providers.market_data import (MarketDataProvider, get_market_data_provider,
                                       ProductNotFound, SnapshotNotFound, ProviderUnavailable)
from app.schemas.market_data import Product, ProductHoldings
from app.utils.auth import get_current_user

router = APIRouter(prefix='/market-data', tags=['market data'], dependencies=[Depends(get_current_user)])
Provider = Annotated[MarketDataProvider, Depends(get_market_data_provider)]


@router.get('/products', response_model=list[Product])
def products(provider: Provider):
    try:
        return provider.list_products()
    except ProviderUnavailable:
        raise HTTPException(status_code=503, detail='Market data provider is unavailable')


@router.get('/products/{product_id}/holdings', response_model=ProductHoldings)
def holdings(product_id: str, provider: Provider, as_of: date | None = Query(None)):
    today = datetime.now(timezone.utc).date()
    if as_of and as_of > today:
        raise HTTPException(status_code=422, detail='Holdings date cannot be in the future')
    try:
        return provider.get_holdings(product_id, as_of or today)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail='Product not found')
    except SnapshotNotFound:
        raise HTTPException(status_code=404, detail='No holdings available on or before this date')
    except ProviderUnavailable:
        raise HTTPException(status_code=503, detail='Market data provider is unavailable')
