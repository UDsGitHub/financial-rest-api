from app.schemas.stocks import Symbol

class Watchlist:
    def __init__(self):
        self.__items: list[Symbol] = []

    def get_items(self) -> list[Symbol]:
        return self.__items

    def has_item(self, symbol: str) -> bool:
        return next((val for val in self.__items if val.symbol == symbol), None) is not None;

    def add_item(self, new_item: Symbol):
        self.__items.append(new_item)
        return self.__items
    
    def remove_item(self, delete_item: str) -> list[Symbol]:
        self.__items = list(filter(lambda item: item.symbol != delete_item, self.__items))
        return self.__items
        
