from typing import List

from telegram import Chat
from telegram.ext import BaseFilter

from bot.models.promo_group import TelegramChannel
from bot.models.promo_group import TelegramUser
from bot.utils.chat import is_media_message


class Filters:
    class _IsMedia(BaseFilter):
        name = 'Filters.is_media'

        def filter(self, message):
            return is_media_message(message)

    is_media = _IsMedia()
    """:obj:`Filter`: Messages sent is a media file."""

    class _InChannel(BaseFilter):
        name = 'Filters.in_channel'

        def filter(self, message):
            return message.chat.type == Chat.CHANNEL

    in_channel = _InChannel()
    """:obj:`Filter`: Messages sent in a channels."""

    @staticmethod
    def text_is(*texts: List[str], lower: bool = False):
        """:obj:`Filter`: Messages text matches given text."""
        if lower:
            texts = list(map(str.lower, texts))

        class TextIs(BaseFilter):
            name = 'Filters.text_is'

            def filter(self, message):
                if lower and message.text:
                    return message.text.lower() in texts
                return message.text in texts

        return TextIs()

    @staticmethod
    def text_is_not(*texts: List[str], lower: bool = False):
        """:obj:`Filter`: Messages text does not matche given text."""
        textis = Filters.text_is(*texts, lower)

        class TextIsNot(BaseFilter):
            name = 'Filters.text_is_not'

            def filter(self, message):
                return not textis.filter(message)

        return TextIsNot()

    class _ChannelMessage(BaseFilter):
        name = 'Filters.channel_message'

        def filter(self, message):
            return message.forward_from_chat and message.forward_from_chat.type == 'channel'

    channel_message = _ChannelMessage()
    """:obj:`Filter`: Message text is name of channel."""

    @staticmethod
    def menu(*menus):
        """:obj:`Filter`: Check if the current user is in the given menu."""

        class MenuIs(BaseFilter):
            name = 'Filters.menu'

            def filter(self, message):
                if not message.from_user:
                    return False
                user = TelegramUser.objects.get(id=message.from_user.id)

                return user.menu in menus

        return MenuIs()
