import re

from django.template.loader import get_template
from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler

from bot.commands import BaseCommand
from bot.commands.group_base import GroupBase
from bot.filters import Filters as OF
from bot.models.promo_group import TelegramChannel, Participant
from bot.models.promo_group import PromoGroup
from bot.utils.chat import build_menu
from bot import MANAGE_GROUPS, MANAGE_GROUP, EDIT_NAME, DELETE_GROUP, ADD_PARTICIPANT


class GroupEditor(GroupBase):
    @BaseCommand.command_wrapper(MessageHandler, filters=OF.menu(MANAGE_GROUPS))
    def manage_group(self, group: str or PromoGroup or None = None):
        if isinstance(group, PromoGroup):
            self.current_group = group
        else:
            name = group or self.message.text
            if name in self.name_blacklist:
                return
            self.current_group = self.get_group(name)

        if not self.current_group:
            return

        menu = build_menu('Edit Name', 'Add Participant',
                          'Disable' if self.current_group.active else 'Enable', 'List Participants',
                          'Edit Topics', 'Edit Participants',
                          'Change Promotion Template', 'Set Date/Time',
                          'Delete',
                          footer_buttons=['Back to list'])

        self.message.reply_text(f'Manage "{self.current_group.name}":', reply_markup=ReplyKeyboardMarkup(menu))
        self.set_menu(MANAGE_GROUP)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.text_is('Edit Name')
                                                          & OF.menu(MANAGE_GROUP)))
    def pre_edit_name(self):
        self.message.reply_text(f'Send me the new name for the group "{self.current_group.name}"',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Cancel')))
        self.set_menu(EDIT_NAME)

    @BaseCommand.command_wrapper(MessageHandler, filters=OF.menu(EDIT_NAME) & OF.text_is_not('Cancel'))
    def edit_name(self):
        name = self.message.text
        if name in self.name_blacklist:
            self.message.reply_text(f'You can\'t name your group "{name}"')
            return

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

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(MANAGE_GROUP)
                                                          & (OF.text_is('Enable')
                                                             | OF.text_is('Disable'))))
    def toggle_active(self):
        self.current_group.active = not self.current_group.active
        self.current_group.save()
        self.message.reply_text(f'Group "{self.current_group.name}" was '
                                f'{"Enabled" if self.current_group.active else "Disabled"}')
        self.manage_group(self.current_group.name)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(MANAGE_GROUP)
                                                          & OF.text_is('Delete')))
    def delete_group(self):
        self.message.reply_text('Are you sure?', reply_markup=ReplyKeyboardMarkup(build_menu('Yes', 'No')))
        self.set_menu(DELETE_GROUP)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(DELETE_GROUP)
                                                          & OF.text_is('Yes')))
    def delete_group_yes(self):
        name = self.current_group.name
        self.current_group.delete()
        self.message.reply_text(f'Group "{name}" has been deleted.')
        self.run_command('mygroups')

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(DELETE_GROUP)
                                                          & OF.text_is('No')))
    def delete_group_no(self):
        self.message.reply_text(f'Cancelled')
        self.manage_group(self.current_group)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.text_is('Add Participant')))
    def add_participant(self):
        self.message.reply_text('Make sure this bot is an admin of the channel you want to add and then forward any '
                                'message from that channel here.',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Cancel')))

        self.set_menu(ADD_PARTICIPANT)

    @BaseCommand.command_wrapper(MessageHandler, filters=OF.channel_message)
    def add_participant_wait(self):
        channel_chat = self.message.forward_from_chat
        channel = TelegramChannel.objects.get_or_create(id=channel_chat.id)[0]
        channel.auto_update_values()

        if Participant.objects.get(promo_group=self.current_group, channel=channel):
            self.message.reply_text(f'The channel "{channel.name}" is already a participant of '
                                    f'"{self.current_group.name}"')
            return

        participant = Participant.objects.create(channel=channel, promo_group=self.current_group, active=True)
        participant.save()

        self.bot.export_chat_invite_link(channel.id)
        self.message.reply_text(f'Participant "{channel.name}" added to "{self.current_group.name}"')
        self.manage_group(self.current_group)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.text_is('Cancel')
                                                          & OF.menu(ADD_PARTICIPANT, EDIT_NAME)))
    def cancel(self):
        if self.current_group:
            self.manage_group(self.current_group)

    @BaseCommand.command_wrapper(MessageHandler, filters=OF.menu(MANAGE_GROUP) & OF.text_is('List Participants'))
    def list_participants(self):
        html = get_template('commands/group_editor/list_participants.html').render({
            'participants': Participant.objects.filter(promo_group=self.current_group)
        })
        html = re.sub('\n+', '\n\n', html)
        self.message.reply_html(html)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(MANAGE_GROUP)
                                                         & OF.text_is('Edit Topics', 'Edit Participants',
                                                                      'Change Promotion Template', 'Set Date/Time')))
    def comming_soon(self):
        self.message.reply_text('Work in progrss')
