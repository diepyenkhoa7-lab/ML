"""Compatibility facade for callers of the original ML02 service extension."""

from .service import MarketService


class CompanyMarketService(MarketService):
    """Inherit company reporting from the shared application service."""
