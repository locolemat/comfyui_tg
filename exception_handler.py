from telebot import ExceptionHandler

class ErrHandler(ExceptionHandler):
    def handle(self, error):
        raise error