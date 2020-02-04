from django.template.loader import get_template
from telegram import ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.utils.chat import build_menu


class Builtins(BaseCommand):

    @BaseCommand.command_wrapper()
    def help(self):
        self.message.reply_html(get_template('commands/builtins/help.html').render())

    @BaseCommand.command_wrapper(CallbackQueryHandler, pattern='^(home|cancel)$')
    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.text_is(['cancel', 'home', 'reset'], lower=True))
    @BaseCommand.command_wrapper(names=['start', 'reset', 'cancel'])
    def start(self):
        if self.update.callback_query:
            self.update.callback_query.answer()
            self.message.delete()

        elif 'start' in self.message.text:
            self.message.reply_html(get_template('commands/builtins/start.html').render())

        if self.message.text.lower() in ['cancel', 'home', 'reset']:
            self.message.reply_text('Current action was cancelled')

        self.telegram_user.current_channel = None
        header, middle, footer = BaseCommand._start_buttons

        buttons = build_menu(*middle, header_buttons=header, footer_buttons=footer)
        self.message.reply_text('What do you want to do?', reply_markup=ReplyKeyboardMarkup(buttons))

    BaseCommand.register_home(start)
