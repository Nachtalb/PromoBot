from django.template.loader import get_template
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackQueryHandler, MessageHandler

from bot.commands import BaseCommand
from bot.models.promo_group import TelegramUser
from bot.filters import Filters as OwnFilters
from bot.utils.chat import build_menu


class Builtins(BaseCommand):

    @BaseCommand.command_wrapper()
    def help(self):
        self.message.reply_html(get_template('commands/builtins/help.html').render())

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^(home|reset)$')
    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.text_is(['home', 'reset'], lower=True))
    @BaseCommand.command_wrapper(names=['start', 'reset'])
    def start(self):
        if self.update.callback_query:
            self.update.callback_query.answer()
            self.message.delete()

        self.telegram_user.current_channel = None
        self.telegram_user.set_menu(TelegramUser.MAIN)

        header, middle, footer = BaseCommand._start_buttons
        menu = build_menu(*middle, header_buttons=header, footer_buttons=footer)
        if not menu:
            buttons = ReplyKeyboardRemove()
        else:
            buttons = ReplyKeyboardMarkup(menu)

        message = self.message.text.strip('/').lower()
        if message in ['home', 'reset']:
            text = 'Current action was cancelled'
        elif message in ['start']:
            text = get_template('commands/builtins/start.html').render()

        self.message.reply_html(text, reply_markup=buttons)

    BaseCommand.register_home(start)
