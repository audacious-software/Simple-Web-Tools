import datetime

import django

from django.contrib.gis import admin

if django.get_version() < '5':
    from django.contrib.gis.admin import OSMGeoAdmin as GISModelAdmin # pylint: disable=no-name-in-module
else:
    from django.contrib.gis.admin import GISModelAdmin # pylint: disable=no-name-in-module

from web_tools.models import UrlContentTracker, RssFeed, RssItem # pylint: disable=wrong-import-position

def reset_last_checked(modeladmin, request, queryset): # pylint: disable=unused-argument
    queryset.update(last_check=datetime.datetime.utcfromtimestamp(0))

reset_last_checked.short_description = 'Reset last checked date'

class UrlContentTrackerAdmin(GISModelAdmin):
    list_display = ('title', 'url', 'last_check', 'check_interval')
    list_filter = ['last_check', 'check_interval']
    search_fields = ['title', 'url', 'last_content']
    actions = [reset_last_checked]

admin.site.register(UrlContentTracker, UrlContentTrackerAdmin)


class RssFeedAdmin(GISModelAdmin):
    list_display = ('title', 'url', 'last_check', 'check_interval')
    list_filter = ['last_check', 'check_interval']
    search_fields = ['title', 'url']

admin.site.register(RssFeed, UrlContentTrackerAdmin)


class RssItemAdmin(GISModelAdmin):
    list_display = ('feed', 'title', 'url', 'date',)
    list_filter = ['date', 'feed']
    search_fields = ['title', 'url', 'content']

admin.site.register(RssItem, RssItemAdmin)
