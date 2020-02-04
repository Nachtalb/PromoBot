# no-autoload
from bot.commands import BaseCommand
from bot.models.promo_group import PromoGroup


class GroupBase(BaseCommand):
    def get_group(self, name):
        return PromoGroup.objects.filter(admins=self.telegram_user, name=name).first()

    @property
    def current_group(self):
        return self.telegram_user.current_group

    @current_group.setter
    def current_group(self, group: PromoGroup):
        self.telegram_user.current_group = group
        self.telegram_user.save(update_fields=['current_group'])
