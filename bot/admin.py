from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText, mark_safe

link_template = '<a href="{link}" target={target}>{text}</a>'
