class ServerAddress:
    def __init__(self, address: str, busy: bool = False, api_port: str = '8100'):
        self.__address = address
        self.__busy = busy
        self.__api_address = self.__address.split(':')[0] + f':{api_port}'

    
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
        
    def api_address(self, api_address: str | None = None) -> str | None :
        if api_address is not None:
            self.__api_address = api_address
        else:
            return self.__api_address
        
    def __str__(self):
        return f'{self.__address} | {"BUSY" if self.__busy else "FREE"} | API: {self.__api_address}'
    
    
    def __repr__(self):
        return self.__str__()


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

    def __str__(self):
        return str(self.__servers)

