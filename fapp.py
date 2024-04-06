from fastapi import Request, FastAPI
from telebot.async_telebot import AsyncTeleBot
from robokassa import check_signature_result
from user_configs import read_config, update_config
from pydantic import BaseModel
from database import DB

import yaml
import sqlite3
import asyncio

class Item(BaseModel):
    OutSum: float
    InvId: int
    Fee: float
    EMail: str
    SignatureValue: str
    PaymentMethod: str
    IncCurrLabel: str


with open('config.yaml') as f:
    config = yaml.safe_load(f)

    BOT_TOKEN = config['network']['BOT_TOKEN']
    MERCHANT_PASSWORD_1 = config['payment']['MERCHANT_PASSWORD_1']

app = FastAPI()

@app.get('/robokassa_result')
async def check_payment(request: Request):
    data = await request.json()

    if not check_signature_result(data['InvId'], data['OutSum'], data['SignatureValue'], MERCHANT_PASSWORD_1):
        return
    

    payments_db = DB('payments.sqlite3')
    payments_db.connect()
    db_result = payments_db.get_payment(data['SignatureValue'])
    payments_db.close()

    #DEBUG
    print(db_result)

    username, user_id = db_result[3], db_result[4]

    user_config = read_config(user_id, username)
    user_config['tokens'] += 10
    update_config(user_id, username, user_config)

    bot = AsyncTeleBot(BOT_TOKEN)

    await bot.send_message(chat_id=user_id, text=f'Your payment has went through! Your token balance is updated to {user_config["tokens"]}')

    

