"""ML02 MarketService extension; parent registers the method on the shared service."""

from .companies import company_report
from .service import MarketService


class CompanyMarketService(MarketService):
    def company_report(self, rows):
        """Audit prepared rows, preserving compensation and label evidence verbatim."""
        return company_report(rows)
