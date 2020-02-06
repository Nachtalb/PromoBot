from typing import Callable

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe

from bot.models import PromoGroup, Participant, TelegramUser, TelegramChannel, Topic


link_template = '<a href="{link}" target={target}>{text}</a>'


def model_link(obj: str, text_field: str) -> SafeText:
    url = reverse(f'admin:bot_{obj.__class__.__name__.lower()}_change', args=(obj.id, ))
    text = getattr(obj, text_field)
    if isinstance(text, Callable):
        text = text()

    return format_html(link_template, link=url, text=text, target='_self')


class TelegramUserAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('id', 'username', 'full_name',)
        }),
        ('Bot State', {
            'fields': ('menu', 'current_group', 'tmp_data'),
        }),
    )

    readonly_fields = ['id',]
    list_display = ['id', 'linked_username', 'full_name', 'channel__names', 'current_group__link', 'modified', 'created']
    list_filter = ['channels']

    def current_group__link(self, obj: TelegramUser) -> SafeText or None:
        if obj.current_group:
            return model_link(obj.current_group, 'name')
        return

    def linked_username(self, obj: TelegramUser) -> SafeText or str:
        if obj.chat and obj.chat.link:
            return format_html(link_template, link=obj.chat.link, text=obj.username_or_name(), target='_blank')
        return obj.username

    def channel__names(self, obj: TelegramUser) -> SafeText:
        return mark_safe(', '.join(map(lambda obj: model_link(obj, 'title'), obj.channels.all())))


admin.site.register(TelegramUser, TelegramUserAdmin)


class TelegramChannelAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('id', 'username', 'title', 'admins')
        }),
    )

    readonly_fields = ['id',]
    list_display = ['id', 'linked_username', 'linked_title', 'linked_admins', 'modified', 'created']
    # list_filter = ['channels']

    def url(self, obj: TelegramChannel) -> str:
        return (obj.chat.link or obj.chat.invite_link) if obj.chat else ''

    def linked_username(self, obj: TelegramChannel) -> SafeText or str:
        if not obj.username:
            return
        if url := self.url(obj):
            return format_html(link_template, link=url, text=obj.username, target='_blank')
        return obj.username

    def linked_title(self, obj: TelegramChannel) -> SafeText or str:
        if url := self.url(obj):
            return format_html(link_template, link=url, text=obj.title, target='_blank')
        return obj.title

    def linked_admins(self, obj: TelegramChannel) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'username_or_name'), obj.admins.all())))


admin.site.register(TelegramChannel, TelegramChannelAdmin)


class PromoGroupAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('name',)
        }),
        ('Settings', {
            'fields': ('admins', 'active', 'template', ),
        }),
    )

    list_display = ['name', 'linked_admins', 'linked_participants', 'linked_topics', 'active', 'modified', 'created']
    # list_filter = ['']

    def linked_admins(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'username_or_name'), obj.admins.all())))

    def linked_participants(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, '__str__'), obj.participants.all())))

    def linked_topics(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'name'), obj.topics.all())))


admin.site.register(PromoGroup, PromoGroupAdmin)


class ParticipantAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('channel', 'promo_group', 'active', 'topic')
        }),
    )

    list_display = ['__str__', 'linked_channel', 'linked_promo_group', 'active', 'linked_topic', 'modified', 'created']
    # list_filter = ['']

    def linked_channel(self, obj: Participant) -> SafeText or None:
        return model_link(obj.channel, 'username_or_title')

    def linked_promo_group(self, obj: Participant) -> SafeText or None:
        return model_link(obj.promo_group, 'name')

    def linked_topic(self, obj: Participant) -> SafeText or None:
        if obj.topic:
            return model_link(obj.topic, 'name')
        return


admin.site.register(Participant, ParticipantAdmin)


class TopicAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('name', 'promo_group')
        }),
    )

    list_display = ['name', 'linked_promo_group']
    # list_filter = ['']

    def linked_promo_group(self, obj: Topic) -> SafeText or None:
        return model_link(obj.promo_group, 'name')


admin.site.register(Topic, TopicAdmin)
