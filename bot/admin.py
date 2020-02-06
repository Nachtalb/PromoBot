from typing import Callable

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe

from bot.models import PromoGroup, Participant, TelegramUser, TelegramChannel, Topic


link_template = '<a href="{link}" target={target}>{text}</a>'


def link(url: str, text: str, new_tab: bool = False) -> str:
    return format_html(link_template, link=url, text=text, target='_blank' if new_tab else '_self')


def model_link(obj: str, text_field: str = None, prefix: str = '', suffix: str = '') -> SafeText:
    url = reverse(f'admin:bot_{obj.__class__.__name__.lower()}_change', args=(obj.id, ))
    if text_field:
        text = getattr(obj, text_field)
        if isinstance(text, Callable):
            text = text()
    else:
        text = ''

    return link(url, f'{prefix}{text}{suffix}'.strip())


class TelegramUserAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('id', 'linked_username', 'linked_name', 'affiliated_groups', 'affiliated_channels')
        }),
        ('Bot State', {
            'fields': ('menu', 'current_group', 'tmp_data'),
        }),
    )

    readonly_fields = ['id', 'linked_username', 'linked_name', 'affiliated_groups', 'affiliated_channels']
    list_display = ['id', 'linked_username', 'full_name', 'linked_channels', 'current_group__link', 'modified', 'created']
    list_filter = ['channels']

    def current_group__link(self, obj: TelegramUser) -> SafeText or None:
        if obj.current_group:
            return model_link(obj.current_group, 'name')
        return

    current_group__link.short_description = 'Current Group'

    def linked_username(self, obj: TelegramUser) -> SafeText or str:
        if obj.chat and obj.chat.link:
            return link(obj.chat.link, obj.username_or_name(), True)
        return obj.username_or_name

    linked_username.short_description = 'Username'

    def linked_channels(self, obj: TelegramUser) -> SafeText:
        return mark_safe(', '.join(map(lambda obj: model_link(obj, 'title'), obj.channels.all())))

    linked_channels.short_description = 'Channels'

    def affiliated_groups(self, obj: TelegramUser) -> SafeText:
        participating = []
        for channel in obj.channels.all():
            for participant in channel.participating.all():
                participating.append(participant.promo_group)

        participating = set(participating)
        admins = set(obj.admins_at.all())

        final_resultset = []
        for group in participating | admins:
            addition = []
            if {group} & admins:
                addition.append('admin')
            if {group} & participating:
                addition.append('participating')
            final_resultset.append(model_link(group, 'name', suffix=f' ({", ".join(addition)})'))

        return mark_safe(', '.join(final_resultset))

    affiliated_groups.short_description = 'Affiliated Promotion Groups'

    def affiliated_channels(self, obj: TelegramUser) -> SafeText:
        return mark_safe(', '.join(map(lambda c: model_link(c, 'title'), obj.channels.all())))

    affiliated_channels.short_description = 'Channels'

    def linked_username(self, obj: TelegramUser) -> SafeText or None:
        if obj.username:
            return link(obj.chat.link, obj.at_username, True)
        return None

    linked_username.short_description = 'Username'

    def linked_name(self, obj: TelegramUser) -> SafeText:
        return link(obj.chat.link, obj.full_name, True)

    linked_name.short_description = 'Full Name'


admin.site.register(TelegramUser, TelegramUserAdmin)


class TelegramChannelAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('id', 'linked_username', 'linked_title', 'admins', 'linked_admins', 'participating_in')
        }),
    )

    readonly_fields = ['id', 'linked_username', 'linked_title', 'participating_in', 'linked_admins']
    list_display = ['id', 'linked_username', 'linked_title', 'linked_admins', 'modified', 'created']

    def url(self, obj: TelegramChannel) -> str:
        return (obj.chat.link or obj.chat.invite_link) if obj.chat else ''

    def linked_username(self, obj: TelegramChannel) -> SafeText or str:
        if not obj.username:
            return
        if url := self.url(obj):
            return link(url, obj.at_username, True)
        return obj.at_username

    linked_username.short_description = 'Username'

    def linked_title(self, obj: TelegramChannel) -> SafeText or str:
        if url := self.url(obj):
            return link(url, obj.title, True)
        return obj.title

    linked_title.short_description = 'Title'

    def linked_admins(self, obj: TelegramChannel) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'username_or_name'), obj.admins.all())))

    linked_admins.short_description = 'Admins'

    def participating_in(self, obj: TelegramChannel) -> SafeText:
        participating = []
        for participant in obj.participating.all():
            participating.append('%s %s' % (model_link(participant.promo_group, 'name'),
                                            model_link(participant, prefix='(P)')))

        return mark_safe(', '.join(participating))

    participating_in.short_description = 'Participating in'


admin.site.register(TelegramChannel, TelegramChannelAdmin)


class PromoGroupAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('name', 'linked_participants', 'linked_topics')
        }),
        ('Settings', {
            'fields': ('admins', 'linked_admins', 'active', 'template', ),
        }),
    )

    readonly_fields = ['linked_participants', 'linked_topics', 'linked_admins']
    list_display = ['name', 'linked_admins', 'linked_participants', 'linked_topics', 'active', 'modified', 'created']

    def linked_admins(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'username_or_name'), obj.admins.all())))

    linked_admins.short_description = 'Admins'

    def linked_participants(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda p: '%s %s' % (model_link(p.channel, 'title'),  model_link(p, prefix='(P)')),
                                       obj.participants.all())))

    linked_participants.short_description = 'Participants'

    def linked_topics(self, obj: PromoGroup) -> SafeText or None:
        return mark_safe(', '.join(map(lambda o: model_link(o, 'name'), obj.topics.all())))

    linked_topics.short_description = 'Topics'


admin.site.register(PromoGroup, PromoGroupAdmin)


class ParticipantAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('linked_channel', 'linked_promo_group', 'active', 'topic')
        }),
    )

    readonly_fields = ['linked_channel', 'linked_promo_group']
    list_display = ['__str__', 'linked_channel', 'linked_promo_group', 'active', 'linked_topic', 'modified', 'created']
    # list_filter = ['']

    def linked_channel(self, obj: Participant) -> SafeText or None:
        return model_link(obj.channel, 'username_or_title')

    linked_channel.short_description = 'Channel'

    def linked_promo_group(self, obj: Participant) -> SafeText or None:
        return model_link(obj.promo_group, 'name')

    linked_promo_group.short_description = 'Promotion Group'

    def linked_topic(self, obj: Participant) -> SafeText or None:
        if obj.topic:
            return model_link(obj.topic, 'name')
        return

    linked_topic.short_description = 'Topic'


admin.site.register(Participant, ParticipantAdmin)


class TopicAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Infos', {
            'fields': ('name', 'promo_group')
        }),
    )

    list_display = ['name', 'linked_promo_group']

    def linked_promo_group(self, obj: Topic) -> SafeText or None:
        return model_link(obj.promo_group, 'name')

    linked_promo_group.short_description = 'Promotion Group'


admin.site.register(Topic, TopicAdmin)
