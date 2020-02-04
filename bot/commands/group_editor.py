from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler

from bot.commands import BaseCommand
from bot.commands.group_base import GroupBase
from bot.filters import Filters as OwnFilters
from bot.models.promo_group import TelegramUser
from bot.utils.chat import build_menu


class GroupEditor(GroupBase):
    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.MANAGE_GROUPS))
    def manage_group(self, group_name=None):
        name = group_name or self.message.text
        self.current_group = self.get_group(name)

        menu = build_menu('Edit Name', 'Add Participant',
                          'Disable' if self.current_group.active else 'Enable', 'Delete',
                          footer_buttons=['Back to list'])

        self.message.reply_text(f'Manage "{self.current_group.name}":', reply_markup=ReplyKeyboardMarkup(menu))
        self.telegram_user.set_menu(TelegramUser.MANAGE_GROUP)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.text_is('Edit Name')
                                                          & OwnFilters.menu(TelegramUser.MANAGE_GROUP)))
    def pre_edit_name(self):
        self.message.reply_text(f'Send me the new name for the group "{self.current_group.name}"')
        self.telegram_user.set_menu(TelegramUser.EDIT_NAME)

    @BaseCommand.command_wrapper(MessageHandler, filters=OwnFilters.menu(TelegramUser.EDIT_NAME))
    def edit_name(self):
        name = self.message.text

        exising = self.get_group(name)
        if name == self.current_group.name:
            self.message.reply_text('The name is the same as before')
            return
        elif exising:
            self.message.reply_text('A group with that name already exists')
            return

        old_name = self.current_group.name
        self.current_group.name = name
        self.current_group.save()

        self.message.reply_text(f'Name changed from "{old_name}" to "{name}"')
        self.manage_group(name)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.menu(TelegramUser.MANAGE_GROUP)
                                                          & (OwnFilters.text_is('Enable')
                                                             | OwnFilters.text_is('Disable'))))
    def toggle_active(self):
        self.current_group.active = not self.current_group.active
        self.current_group.save()
        self.message.reply_text(f'Group "{self.current_group.name}" was '
                                f'{"Enabled" if self.current_group.active else "Disabled"}')
        self.manage_group(self.current_group.name)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OwnFilters.text_is('Add Participant')
                                                          | OwnFilters.text_is('Delete')))
    def comming_soon(self):
        self.message.reply_text('Comming soon...')
