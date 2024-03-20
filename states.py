from telebot.asyncio_handler_backends import State, StatesGroup


class BotStates(StatesGroup):
    text_to_video = State()
    image_to_video = State()
    text_aspect_ratio = State()
    video_aspect_ratio = State()