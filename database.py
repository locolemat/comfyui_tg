import sqlite3
import os

class DB:
    def __init__(self, path: str):
        self.__path = os.path.join(os.path.dirname(__file__), path)
        self.__connection = None


    def connect(self):
        if self.__connection is None:
            self.__connection = sqlite3.connect(self.__path)
            return self.__connection
        return None
    

    def close(self):
        if self.__connection is not None:
            self.__connection.close()
            self.__connection = None
        

    def cursor(self):
        if self.__connection is not None:
            return self.__connection.cursor()
        

    def commit(self):
        if self.__connection is not None:
            self.__connection.commit()

        
    def add_payment(self, out_sum: int, signature: str, username: str, user_id: str, table: str = 'payments'):
        self.cursor().execute(f'INSERT INTO {table} (out_sum, signature, username, user_id) VALUES (?, ?, ?, ?)', (out_sum, signature, username, user_id))
        self.commit()


    def get_payment(self, signature: str, table:str = 'payments'):
        cursor = self.cursor()
        cursor.execute(f'SELECT * FROM {table} WHERE signature = {signature}')
        return cursor.fetchone()
    
    def get_last_inv_id(self, table: str = 'payments'):
        cursor = self.cursor()
        cursor.execute(f"SELECT * FROM {table} ORDER BY inv_id DESC LIMIT 1")
        return cursor.fetchone()