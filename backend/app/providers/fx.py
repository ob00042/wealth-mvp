"""Replaceable FX provider; the demo adapter reads local fictional fixtures."""
import json
from datetime import date
from pathlib import Path
from typing import Protocol
from app.schemas.fx import FxSnapshot, FxRates


class FxSnapshotNotFound(Exception):
    pass


class FxProviderUnavailable(Exception):
    pass


class FxProvider(Protocol):
    source: str
    synthetic: bool
    stale_after_days: int

    def supported_currencies(self) -> list[str]: ...
    def get_rates(self, as_of: date) -> FxRates: ...


class FictionalFxProvider:
    source = 'Fictional FX dataset v1'
    synthetic = True
    stale_after_days = 45

    def __init__(self, fixture_path: Path | None = None):
        path = fixture_path or Path(__file__).parent / 'fixtures' / 'fx.json'
        self.snapshots = [FxSnapshot.model_validate(row) for row in json.loads(path.read_text())]
        dates = [row.as_of_date for row in self.snapshots]
        if not dates or len(dates) != len(set(dates)):
            raise ValueError('FX fixtures require unique dated snapshots')

    def supported_currencies(self):
        return sorted({code for snapshot in self.snapshots for code in snapshot.rates})

    def get_rates(self, as_of):
        snapshots = [row for row in self.snapshots if row.as_of_date <= as_of]
        if not snapshots:
            raise FxSnapshotNotFound()
        snapshot = max(snapshots, key=lambda row: row.as_of_date)
        age = (as_of - snapshot.as_of_date).days
        return FxRates(**snapshot.model_dump(), requested_as_of=as_of,
                       source=self.source, synthetic=self.synthetic,
                       supported_currencies=self.supported_currencies(), age_days=age,
                       stale=age > self.stale_after_days, stale_after_days=self.stale_after_days)


def get_fx_provider() -> FxProvider:
    return _provider


_provider = FictionalFxProvider()
