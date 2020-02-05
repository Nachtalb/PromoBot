from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler

from bot.commands import BaseCommand
from bot.commands.group_base import GroupBase
from bot.filters import Filters as OwnFilters
from bot.models.promo_group import TelegramUser
from bot.models.promo_group import PromoGroup
from bot.utils.chat import build_menu


class GroupManager(GroupBase):
    @BaseCommand.command_wrapper()
    def new(self):
        self.message.reply_text('What is he name of the Promotion Group?')
        self.telegram_user.set_menu(TelegramUser.NEW_PG_Q_1)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.NEW_PG_Q_1))
    def create_pg(self):
        name = self.message.text
        if name in self.name_blacklist:
            self.message.reply_text(f'You can\'t name your group "{name}"')
            return

        if self.get_group(name):
            self.message.reply_text(f'A group with the name "{name}" does already exist')
            return

        promo_group = PromoGroup.objects.create(name=name)
        promo_group.admins.add(self.telegram_user)
        promo_group.save()

        self.message.reply_text('Okay got it. I have created a new Promotion Group.')
        self.telegram_user.set_menu(TelegramUser.MAIN)
        self.mygroups()

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.text_is('Back to list'))
    @BaseCommand.command_wrapper()
    def mygroups(self):
        names = map(lambda o: o.name, PromoGroup.objects.filter(admins=self.telegram_user))
        menu = build_menu(*names)
        self.message.reply_text('Promotion Groups:', reply_markup=ReplyKeyboardMarkup(menu))
        self.telegram_user.tmp_data = ''
        self.telegram_user.set_menu(TelegramUser.MANAGE_GROUPS)
