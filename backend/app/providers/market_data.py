"""Provider contract and a deterministic local implementation. No Bloomberg connection."""
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Protocol
from app.schemas.market_data import Product, HoldingsSnapshot, ProductHoldings


class ProductNotFound(Exception):
    pass


class SnapshotNotFound(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


class MarketDataProvider(Protocol):
    def list_products(self) -> list[Product]: ...
    def get_holdings(self, product_id: str, as_of: date) -> ProductHoldings: ...


class FictionalMarketDataProvider:
    """Independent security IDs, exact decimal weights, no inferred/made-up remainder.

    The fixture is validated at startup. A future adapter maps a vendor response to
    these models; it must not expose vendor credentials or raw SDK objects to the UI.
    """
    stale_after_days = 45

    def __init__(self, fixture_path: Path | None = None):
        path = fixture_path or Path(__file__).parent / 'fixtures' / 'products.json'
        data = json.loads(path.read_text())
        products = [Product.model_validate(p) for p in data['products']]
        self.products = {p.id: p for p in products}
        if len(self.products) != len(products):
            raise ValueError('Duplicate product identifier')
        self.snapshots = [HoldingsSnapshot.model_validate(s) for s in data['snapshots']]
        keys = [(s.product_id, s.as_of_date) for s in self.snapshots]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate dated snapshot')
        if any(s.product_id not in self.products for s in self.snapshots):
            raise ValueError('Snapshot references unknown product')

    def list_products(self):
        return sorted(self.products.values(), key=lambda p: p.name)

    def get_holdings(self, product_id, as_of):
        product = self.products.get(product_id)
        if product is None:
            raise ProductNotFound(product_id)
        snapshots = [s for s in self.snapshots if s.product_id == product_id and s.as_of_date <= as_of]
        if not snapshots:
            raise SnapshotNotFound(product_id)
        snapshot = max(snapshots, key=lambda s: s.as_of_date)
        coverage = sum((h.weight for h in snapshot.holdings), Decimal(0))
        age = (as_of - snapshot.as_of_date).days
        return ProductHoldings(product=product, as_of_date=snapshot.as_of_date,
                               requested_as_of=as_of, available_dates=sorted(s.as_of_date for s in snapshots),
                               age_days=age, stale=age > self.stale_after_days,
                               stale_after_days=self.stale_after_days, coverage=coverage,
                               unreported_weight=Decimal(1) - coverage, holdings=snapshot.holdings)


# FastAPI dependency: tests and future integrations can replace this provider.
def get_market_data_provider() -> MarketDataProvider:
    return _provider


_provider = FictionalMarketDataProvider()
