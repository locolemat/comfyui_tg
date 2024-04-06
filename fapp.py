from fastapi import FastAPI
from telebot.async_telebot import AsyncTeleBot
from robokassa import check_signature_result, calculate_signature
from user_configs import read_config, update_config
from pydantic import BaseModel
from database import DB

import yaml
import sqlite3
import asyncio
import logging

class Item(BaseModel):
    OutSum: float
    InvId: int
    Fee: float
    EMail: str
    SignatureValue: str
    PaymentMethod: str
    IncCurrLabel: str

logging.basicConfig(level=logging.DEBUG, filename="fapp.log",filemode="a")

with open('config.yaml') as f:
    config = yaml.safe_load(f)

    BOT_TOKEN = config['network']['BOT_TOKEN']
    MERCHANT_LOGIN = config['payment']['MERCHANT_LOGIN']
    MERCHANT_PASSWORD_1 = config['payment']['MERCHANT_PASSWORD_1']
    MERCHANT_PASSWORD_2 = config['payment']['MERCHANT_PASSWORD_2']
    COST = config['payment']['COST']


app = FastAPI()

@app.get('/robokassa_result')
async def check_payment(InvId: int, OutSum: float, SignatureValue: str, PaymentMethod: str, IncSum: float, IncCurrLabel: str, EMail: str, Fee: float):
    logging.debug('I got a request!')

    data = {"InvId": InvId,
            "OutSum": OutSum,
            "SignatureValue": SignatureValue,
            "PaymentMethod": PaymentMethod,
            "IncSum": IncSum,
            "IncCurrLable": IncCurrLabel,
            "EMail": EMail,
            "Fee": Fee}
    
    logging.debug('I got data!')
    logging.debug(f'It\'s of type {type(data)}')
    logging.debug(f'Here it is: {data}')

    # if not check_signature_result(data['InvId'], data['OutSum'], data['SignatureValue'], MERCHANT_PASSWORD_2):
    #     logging.debug('It isnt that obvious this time around')
    #     return
    
    logging.debug('Trying to get DB data')
    payments_db = DB('payments.sqlite3')
    payments_db.connect()
    db_result = payments_db.get_payment(data['InvId'])
    payments_db.close()

    #DEBUG
    logging.debug(db_result)

    username, user_id = db_result[3], db_result[4]

    user_config = read_config(user_id, username)
    user_config['tokens'] += 10
    update_config(user_id, username, user_config)

    bot = AsyncTeleBot(BOT_TOKEN)

    await bot.send_message(chat_id=user_id, text=f'Your payment has went through! Your token balance is updated to {user_config["tokens"]}')

    

