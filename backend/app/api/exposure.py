from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.history import history_client
from app.providers.market_data import get_market_data_provider
from app.services.exposure import analyse_exposure
from app.schemas.exposure import PortfolioExposure

router = APIRouter(prefix='/clients', tags=['portfolio exposure'])


@router.get('/{client_ref}/exposure', response_model=PortfolioExposure)
def exposure(client=Depends(history_client), provider=Depends(get_market_data_provider),
             currency: str = Query(..., pattern='^[A-Z]{3}$'), as_of: date | None = None):
    today = datetime.now(timezone.utc).date()
    cutoff = as_of or today
    if cutoff > today:
        raise HTTPException(status_code=422, detail='Composition cutoff cannot be in the future')
    try:
        return analyse_exposure(client, currency, cutoff, provider)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
