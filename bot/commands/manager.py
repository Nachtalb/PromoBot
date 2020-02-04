from django.template.loader import get_template
from telegram import ReplyKeyboardMarkup
from telegram.ext import CallbackQueryHandler, MessageHandler

from bot.commands import BaseCommand
from bot.filters import Filters as OwnFilters
from bot.models.promo_group import TelegramUser
from bot.models.promo_group import PromoGroup
from bot.utils.chat import build_menu

import json


class Builtins(BaseCommand):
    def get_group(self, name):
        return PromoGroup.objects.filter(admins=self.telegram_user, name=name).first()

    @BaseCommand.command_wrapper()
    def new(self):
        self.message.reply_text('What is he name of the Promotion Group?')
        self.telegram_user.set_menu(TelegramUser.NEW_PG_Q_1)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.NEW_PG_Q_1))
    def create_pg(self):
        name = self.message.text
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

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.MANAGE_GROUPS))
    def manage_group(self, group_name=None):
        name = group_name or self.message.text
        group = self.get_group(name)

        menu = build_menu('Edit Name', 'Add Participant', 'Disable' if group.active else 'Enable', 'Delete',
                         footer_buttons=['Back to list'])

        self.telegram_user.tmp_data = str(group.name)

        self.message.reply_text(f'Manage "{group.name}":', reply_markup=ReplyKeyboardMarkup(menu))
        self.telegram_user.set_menu(TelegramUser.MANAGE_GROUP)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.text_is('Edit Name')
                                                          & OwnFilters.menu(TelegramUser.MANAGE_GROUP)))
    def pre_edit_name(self):
        group = self.get_group(self.telegram_user.tmp_data)
        self.message.reply_text(f'Send me the new name for the group "{group.name}"')
        self.telegram_user.set_menu(TelegramUser.EDIT_NAME)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.EDIT_NAME))
    def edit_name(self):
        name = self.message.text

        exising = self.get_group(name)
        current = self.get_group(self.telegram_user.tmp_data)

        if name == current.name:
            self.message.reply_text('The name is the same as before')
            return
        elif exising:
            self.message.reply_text('A group with that name already exists')
            return

        old_name = current.name
        current.name = name
        current.save()
        self.message.reply_text(f'Name changed from "{old_name}" to "{name}"')
        self.manage_group(name)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.menu(TelegramUser.MANAGE_GROUP)
                                                          & (OwnFilters.text_is('Enable')
                                                             | OwnFilters.text_is('Disable'))))
    def toggle_active(self):
        group = self.get_group(self.telegram_user.tmp_data)
        group.active = not group.active
        group.save()
        self.message.reply_text(f'Group "{group.name}" was {"Enabled" if group.active else "Disabled"}')
        self.manage_group(group.name)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.text_is('Add Participant')
                                                          | OwnFilters.text_is('Delete')))
    def comming_soon(self):
        self.message.reply_text('Comming soon...')
