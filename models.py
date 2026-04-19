# pylint: disable=no-member, line-too-long

# -*- coding: utf-8 -*-
import datetime
import difflib
import re
import time

import cloudscraper
import feedparser
import pytz

from django.conf import settings
from django.contrib.gis.db import models
from django.core.mail import EmailMultiAlternatives, send_mail
from django.utils import timezone


class UrlContentTracker(models.Model):
    objects = models.Manager()

    title = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024)
    replace_pattern = models.TextField(max_length=1024, null=True, blank=True)
    last_content = models.TextField(max_length=(1048576 * 2), blank=True, default='')
    last_check = models.DateTimeField()
    check_interval = models.IntegerField(default=4)
    change_size = models.IntegerField(default=0)

    ignore_http_errors = models.BooleanField(default=False)

    def needs_check(self):
        now = timezone.now()

        interval = datetime.timedelta(hours=self.check_interval)

        if self.last_check is None or now - self.last_check > interval:
            return True

        return False

    def do_check(self):
        scraper = cloudscraper.create_scraper()

        response = scraper.get(self.url)

        content = response.text # opener.open(request).read().decode('utf-8')

        if 200 <= response.status_code < 300:
            for pattern in self.replace_pattern.splitlines():
                if pattern is not None and pattern.strip():
                    content = re.sub(pattern, '', content, flags=re.DOTALL|re.MULTILINE)

            diffs = difflib.unified_diff(self.last_content.splitlines(), content.splitlines())

            diff_content = ''

            for diff in diffs:
                diff_content += (diff + '\n')

            if diff_content != '' and len(diff_content) > self.change_size:
                self.last_content = content

                send_to = ['chris@audacious-software.com']

                send_mail('[AS] Updated: ' + self.title, diff_content, 'robot@audacious-software.com', send_to, fail_silently=False)
        else:
            if self.ignore_http_errors is False:
                print('Unable to parse URL: %s -  %s' % (self.url, response.status_code))
                print(response.text)

        self.last_check = timezone.now()
        self.save()


class RssFeed(models.Model):
    objects = models.Manager()

    title = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024)

    last_check = models.DateTimeField()
    check_interval = models.IntegerField(default=4)

    def needs_check(self):
        now = timezone.now()

        interval = datetime.timedelta(hours=self.check_interval)

        if self.last_check is None or now - self.last_check > interval:
            return True

        return False

    def do_check(self):
        feed = feedparser.parse(self.url, agent='Audacious Software/1.0 +https://audacious-software.com/')

        for entry in feed['entries']:
            # print('ENTRY: ' + str(entry))
            url = entry['link']

            if entry['id'].startswith('http'):
                url = entry['id']

            if self.items.filter(url=url).count() == 0:
                item = RssItem(feed=self)

                item.url = url
                item.title = entry['title']

                item.content = entry['summary_detail']['value']

                if entry['content'] and 'value' in entry['content'][0]:
                    item.content = entry['content'][0]['value']

                local_tz = pytz.timezone(settings.TIME_ZONE)

                item.date = datetime.datetime.fromtimestamp(time.mktime(entry['published_parsed']), local_tz)

                item.save()

                send_to = ['chris@audacious-software.com']

                html_content = None

                if item.content.startswith('<'):
                    html_content = '<p>URL: <a href="' + url + '">' + url + '</a></p>' + item.content

                msg = EmailMultiAlternatives('[AS] RSS Item: ' + item.title + ' (' + self.title + ')', item.content + '\n\n' + url, 'robot@audacious-software.com', send_to)

                if html_content is not None:
                    msg.attach_alternative(html_content, "text/html")

                msg.send()

        self.last_check = timezone.now()

        self.save()


class RssItem(models.Model):
    objects = models.Manager()

    feed = models.ForeignKey(RssFeed, related_name='items', on_delete=models.CASCADE)

    title = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024)
    content = models.TextField(max_length=1048576, null=True, blank=True)

    date = models.DateTimeField()
