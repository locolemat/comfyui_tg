
class QueueItem:
    def __init__(self, user: int, prompt: str, username: str):
        self.__user = user
        self.__prompt = prompt
        self.__username = username

    
    def get_user(self) -> int:
        return self.__user
    
    def get_username(self) -> str:
        return self.__username

    def get_prompt(self) -> str:
        return self.__prompt

    def __eq__(self, other):
        if self.__user == other.__user:
            return True
        return False
    

    def __str__(self):
        return f'{self.__address} {self.__user}' 
    

    def __repr__(self):
        return self.__str__()


class Queue:
    def __init__(self):
        self.__items = []


    def get_length(self) -> int:
        return len(self.__items)


    def get_items(self) -> list[QueueItem]:
        return self.__items

    def find_queue_item_by_user(self, user: int) -> QueueItem:
        for index in range(len(self.__items)):
            if self.__items[index].get_user() == user:
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
    

    def __str__(self):
        return str(self.__items)

    
    



