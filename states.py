from telebot.asyncio_handler_backends import State, StatesGroup


class BotStates(StatesGroup):
    text_to_image = State()
    image_to_video = State()