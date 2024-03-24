from server_address import ServerAddress

class QueueItem:
    def __init__(self, address: ServerAddress, user: str):
        self.__address = address
        self.__user = user

    
    def get_user(self) -> str:
        return self.__user
    

    def get_address(self) -> ServerAddress:
        return self.__address
    

    def __eq__(self, other):
        if self.__address.address() == other.__address.address() and self.__user == other.__user:
            return True
        return False


class Queue:
    def __init__(self):
        self.__items = []


    def get_length(self) -> int:
        return len(self.__items)


    def get_items(self) -> list[QueueItem]:
        return self.__items

    def find_queue_item_by_username(self, username: str) -> QueueItem:
        for index in range(len(self.__items)):
            if self.__items[index].get_user() == username:
                return self.__items[index]

        return None
    

    def add_to_queue(self, item: QueueItem):
        self.__items.append(item)

    
    def advance_queue(self):
        self.__items.pop(0)
        # notify remaining people in the queue their position has advanced

    
    def determine_pos(self, item: QueueItem) -> int | None:
        for index in range(len(self.__items)):
            if item == self.__items[index]:
                return index
            
        return None

    
    



