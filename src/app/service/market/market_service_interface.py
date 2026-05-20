from abc import ABC, abstractmethod


class IMarketService(ABC):
    @abstractmethod
    async def get_market_status(self, ip: str, region: str | None = None):
        pass
