from telegram import ReplyKeyboardMarkup
from telegram.ext import MessageHandler

from bot.commands import BaseCommand
from bot.commands.group_base import GroupBase
from bot.filters import Filters as OF
from bot.models.promo_group import PromoGroup
from bot.utils.chat import build_menu
from bot import NEW_PG_Q_1, MAIN, MANAGE_GROUPS


class GroupManager(GroupBase):
    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(MANAGE_GROUPS)
                                                          & OF.text_is('New Group')))
    @BaseCommand.command_wrapper()
    def new(self):
        self.message.reply_text('What is he name of the Promotion Group?',
                                reply_markup=ReplyKeyboardMarkup(build_menu('Cancel')))
        self.set_menu(NEW_PG_Q_1)

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.menu(NEW_PG_Q_1)
                                                          & OF.text_is_not('Cancel')))
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
        self.set_menu(MAIN)
        self.mygroups()

    @BaseCommand.command_wrapper(MessageHandler, filters=(OF.text_is('Back to list')
                                                          | (OF.text_is('Cancel')
                                                             & OF.menu(NEW_PG_Q_1))))
    @BaseCommand.command_wrapper()
    def mygroups(self):
        self.current_group = None
        self.set_menu(MANAGE_GROUPS)

        names = list(map(lambda o: o.name, PromoGroup.objects.filter(admins=self.telegram_user)))
        menu = build_menu(*names, footer_buttons=['New Group'])
        if len(menu) == 1:
            text = 'No Promoion Groups created yet. Use /new to create a new one.'
        else:
            text = 'Promotion Groups'

        self.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(menu))
