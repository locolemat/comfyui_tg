from telebot.asyncio_handler_backends import State, StatesGroup


class BotStates(StatesGroup):
    generate = State()
    text_aspect_ratio = State()
    video_aspect_ratio = State()