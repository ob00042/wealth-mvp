from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.history import history_client
from app.services.fx import translate_portfolio
from app.schemas.fx import ReportingValuation, FxRates
from app.providers.fx import get_fx_provider, FxProviderUnavailable, FxSnapshotNotFound
from app.utils.auth import get_current_user

router = APIRouter(prefix='/clients', tags=['reporting valuation'])


@router.get('/{client_ref}/reporting-valuation', response_model=ReportingValuation)
def reporting_valuation(client=Depends(history_client), provider=Depends(get_fx_provider),
                        currency: str = Query('EUR', pattern='^[A-Z]{3}$'), as_of: date | None = None):
    today = datetime.now(timezone.utc).date()
    cutoff = as_of or today
    if cutoff > today:
        raise HTTPException(status_code=422, detail='FX cutoff cannot be in the future')
    try:
        return translate_portfolio(client, currency, cutoff, provider)
    except FxProviderUnavailable:
        raise HTTPException(status_code=503, detail='FX provider is unavailable')
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


rates_router = APIRouter(prefix='/market-data/fx', tags=['FX market data'],
                         dependencies=[Depends(get_current_user)])


@rates_router.get('/rates', response_model=FxRates)
def rates(provider=Depends(get_fx_provider), as_of: date | None = None):
    today = datetime.now(timezone.utc).date()
    cutoff = as_of or today
    if cutoff > today:
        raise HTTPException(status_code=422, detail='FX cutoff cannot be in the future')
    try:
        return provider.get_rates(cutoff)
    except FxSnapshotNotFound:
        raise HTTPException(status_code=404, detail='No FX rates available on or before this date')
    except FxProviderUnavailable:
        raise HTTPException(status_code=503, detail='FX provider is unavailable')
