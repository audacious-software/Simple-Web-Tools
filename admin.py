import datetime

from django.contrib import admin

from .models import UrlContentTracker, RssFeed, RssItem # pylint: disable=wrong-import-position

def reset_last_checked(modeladmin, request, queryset): # pylint: disable=unused-argument
    queryset.update(last_check=datetime.datetime.utcfromtimestamp(0))

reset_last_checked.short_description = 'Reset last checked date'

class UrlContentTrackerAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'last_check', 'check_interval')
    list_filter = ['last_check', 'check_interval']
    search_fields = ['title', 'url', 'last_content']
    actions = [reset_last_checked]

admin.site.register(UrlContentTracker, UrlContentTrackerAdmin)

class RssFeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'last_check', 'check_interval')
    list_filter = ['last_check', 'check_interval']
    search_fields = ['title', 'url']

admin.site.register(RssFeed, UrlContentTrackerAdmin)

class RssItemAdmin(admin.ModelAdmin):
    list_display = ('feed', 'title', 'url', 'date',)
    list_filter = ['date', 'feed']
    search_fields = ['title', 'url', 'content']

admin.site.register(RssItem, RssItemAdmin)
