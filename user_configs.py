from telebot.types import Chat

import yaml
import os

def add_config(data: Chat, USER_CONFIGS_LOCATION: str, INITIAL_TOKEN_AMOUNT: int) -> bool:
    """
    Добавить конфиг пользователя по данным о нём из бота

    Принимает message.chat в качестве параметра

    Возвращает False, если конфиг с таким айди уже существует
    """
    filename = f'{USER_CONFIGS_LOCATION}/config_{data.id}_{data.username}.yaml'

    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            user_data = {'id': data.id, 
                         'username': data.username, 
                         'first_name': data.first_name, 
                         'last_name': data.last_name,
                         'tokens': INITIAL_TOKEN_AMOUNT}

            yaml.dump(user_data, f)
            return True
        
    return False

def read_config(user: int, username: str, USER_CONFIGS_LOCATION: str) -> dict:
    """
    Прочитать конфиг пользователя по данному Телеграм ID.

    Возвращает пустой словарь, если конфиг указанного пользователя не существует.
    """
    filename = f'{USER_CONFIGS_LOCATION}/config_{user}_{username}.yaml'

    if not os.path.exists(filename):
        return {}
    else:
        with open(filename, 'r') as f:
            return yaml.safe_load(f)
    

def update_config(user: int, username: str, data: dict, USER_CONFIGS_LOCATION: str) -> bool:
    """
    Обновить конфиг указанного по Телеграм ID пользователя.

    Принимает ID и словарь - новый желаемый конфиг.

    Возвращает False, если указанного пользователя не существует.
    """
    filename = f'{USER_CONFIGS_LOCATION}/config_{user}_{username}.yaml'

    if not os.path.exists(filename):
        return False
    else:
        with open(filename, 'w') as f:
            yaml.dump(data, f)
            return True