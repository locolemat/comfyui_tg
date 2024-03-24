from queue_system import Queue

class ServerAddress:
    def __init__(self, address: str, queue: Queue, busy: bool = False):
        self.__address = address
        self.__busy = busy
        self.__queue = queue

    
    def busy(self, busy: bool | None = None) -> bool | None :
        if busy is not None:
            self.__busy = busy
        else:
            return self.__busy
        
    
    def address(self, address: str | None = None) -> str | None :
        if address is not None:
            self.__address = address
        else:
            return self.__address
        

    def get_queue(self) -> Queue:
        return self.__queue


class ServerAddressController:
    def __init__(self, servers: list[ServerAddress]):
        self.__servers = servers


    def find_available_server(self) -> ServerAddress | None:
        for server in self.__servers:
            if not server.busy():
                return server
            
    
    def servers(self) -> list[ServerAddress]:
        return self.__servers
    

    def add_server(self, server: ServerAddress):
        self.__servers.append(server)


    def find_shortest_queue(self) -> Queue:
        queues = [server.get_queue() for server in self.__servers]
        queues_lengths = {queue: queue.get_length() for queue in queues}

        return sorted(queues_lengths.items(), key=lambda x: x[1])[0]
