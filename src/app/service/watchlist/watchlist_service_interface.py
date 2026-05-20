from abc import ABC, abstractmethod


class IWatchlistService(ABC):
    @abstractmethod
    async def get_items(self, ip: str):
        pass

    @abstractmethod
    async def add_item(self, ip: str, symbol: str):
        pass

    @abstractmethod
    async def remove_item(self, ip: str, symbol: str):
        pass