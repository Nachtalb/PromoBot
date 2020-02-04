from django.db import models
from django_extensions.db.models import TimeStampedModel
from telegram import Chat

from bot.utils.internal import bot_not_running_protect


class TelegramChat:
    _chat = None

    auto_update = []

    @property
    @bot_not_running_protect
    def chat(self):
        if not self._chat:
            from bot.telegrambot import my_bot
            self._chat = my_bot.bot.get_chat(self.id)
        return self._chat

    def save(self, **kwargs):
        if kwargs.get('auto_update', False):
            self.auto_update_values(save=False)
            kwargs.pop('auto_update')
        super().save(**kwargs)

    def auto_update_values(self, chat: Chat = None, save=True) -> bool:
        chat = chat or self.chat
        if chat:
            for name in self.auto_update:
                setattr(self, name, getattr(chat, name))

            if save:
                self.save()
            return True


class PromoGroup(TimeStampedModel):
    admins = models.ManyToManyField('TelegramUser', related_name='admins_at')
    name = models.fields.CharField(max_length=200)
    participant = models.ManyToManyField('Participant', related_name='promo_groups', blank=True)
    active = models.fields.BooleanField(default=False)

    template = models.fields.TextField(blank=True, default='')


class Participant(TimeStampedModel):
    channel = models.ForeignKey('TelegramChannel', on_delete=models.CASCADE, related_name='participating')
    promo_group = models.ForeignKey('PromoGroup', on_delete=models.CASCADE, related_name='participants')

    active = models.fields.BooleanField(default=True)
    topic = models.ForeignKey('Topic', on_delete=models.SET_NULL, blank=True, null=True)


class TelegramUser(TimeStampedModel, TelegramChat):
    auto_update = ['username', 'full_name']

    MAIN = 'main'
    NEW_PG_Q_1 = 'new promo group question 1'
    MANAGE_GROUPS = 'manage groups'
    MANAGE_GROUP = 'manage group'
    EDIT_NAME = 'edit name'

    MENUS = [MAIN, NEW_PG_Q_1, MANAGE_GROUPS, MANAGE_GROUP]

    id = models.fields.BigIntegerField(primary_key=True)
    username = models.fields.CharField(max_length=200, blank=True, null=True)
    full_name = models.fields.CharField(max_length=200)

    menu = models.fields.CharField(max_length=100,
                                   default=MAIN,
                                   verbose_name='Menu',
                                   help_text=', '.join(MENUS))
    current_group = models.ForeignKey('PromoGroup',
                                      on_delete=models.SET_NULL,
                                      related_name='current_at',
                                      blank=True,
                                      null=True)

    tmp_data = models.fields.TextField(default='')

    def __str__(self):
        return self.full_name

    @property
    def name(self) -> str:
        return self.__str__()

    def set_menu(self, menu):
        self.menu = menu
        self.save()


class TelegramChannel(TimeStampedModel, TelegramChat):
    auto_update = ['username', 'title']

    id = models.fields.BigIntegerField(primary_key=True)
    username = models.fields.CharField(max_length=200, blank=True, null=True)
    title = models.fields.CharField(max_length=200, blank=True, null=True)

    admins = models.ManyToManyField('TelegramUser', related_name='channels')

    def __str__(self):
        return self.title

    @property
    def name(self) -> str:
        return self.__str__()


class Topic(TimeStampedModel):
    name = models.fields.CharField(max_length=200)
    promo_group = models.ForeignKey('PromoGroup', on_delete=models.CASCADE, related_name='topics')
