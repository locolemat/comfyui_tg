from fastapi import FastAPI
from telebot.async_telebot import AsyncTeleBot
from robokassa import check_signature_result
from user_configs import read_config, update_config

import yaml
import sqlite3
import asyncio

app = FastAPI()

@app.get('/robokassa_result')
async def check_payment():
    pass
