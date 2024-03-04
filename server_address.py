class ServerAddress:
    def __init__(self, address: str, busy: bool = False):
        self.__address = address
        self.__busy = busy

    
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





