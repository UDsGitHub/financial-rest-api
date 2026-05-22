from app.schemas.stocks import Symbol

class Watchlist:
    def __init__(self):
        self.__items: dict[str, list[Symbol]] = {}

    def get_items(self, ip: str) -> list[Symbol]:
        if ip not in self.__items:
            self.__items[ip] = []
        return self.__items[ip]

    def get_symbols(self, ip: str) -> list[str]:
        return [item.symbol for item in self.get_items(ip)]

    def has_item(self, ip: str, symbol: str) -> bool:
        if ip not in self.__items:
            return False
        return next((val for val in self.__items[ip] if val.symbol == symbol), None) is not None;

    def add_item(self, ip: str, new_item: Symbol):
        if ip not in self.__items:
            self.__items[ip] = []
        self.__items[ip].append(new_item)
        return self.__items[ip]
    
    def remove_item(self, ip: str, delete_item: str) -> dict[str, Symbol]:
        if ip not in self.__items:
            self.__items[ip] = []
            return self.__items[ip]

        self.__items[ip] = list(filter(lambda item: item.symbol != delete_item, self.__items[ip]))
        return self.__items[ip]
        
