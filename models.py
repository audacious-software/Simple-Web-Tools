# pylint: disable=no-member, line-too-long

# -*- coding: utf-8 -*-
import datetime
import difflib
import logging
import re
import time

import cloudscraper
import feedparser
import pytz

from django.conf import settings
from django.db import models
from django.core.mail import EmailMultiAlternatives, send_mail
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__) # pylint: disable-invalid-name

class UrlContentTracker(models.Model):
    class Meta: # pylint: disable=too-few-public-methods, old-style-class, no-init
        verbose_name = 'URL content tracker'
        verbose_name_plural = 'URL content trackers'

    objects = models.Manager()

    title = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024)
    replace_pattern = models.TextField(max_length=1024, null=True, blank=True)
    last_content = models.TextField(max_length=(1048576 * 2), blank=True, default='')
    last_check = models.DateTimeField()
    check_interval = models.IntegerField(default=4)
    change_size = models.IntegerField(default=0)

    ignore_http_errors = models.BooleanField(default=False)

    def __str__(self):
        return '%s' % self.title

    def get_absolute_url(self):
        return reverse('simple_web_tools_url_update', args=[self.pk])

    def needs_check(self):
        now = timezone.now()

        interval = datetime.timedelta(hours=self.check_interval)

        if self.last_check is None or now - self.last_check > interval:
            return True

        return False

    def do_check(self, content=None):
        status_code = 0

        message = None

        if content is None:
            scraper = cloudscraper.create_scraper()

            response = scraper.get(self.url)

            content = response.text # opener.open(request).read().decode('utf-8')
            status_code = response.status_code
        else:
            status_code = 200 # Simulate successful request

        if 200 <= status_code < 300:
            for pattern in self.replace_pattern.splitlines():
                if pattern is not None and pattern.strip():
                    content = re.sub(pattern, '', content, flags=re.DOTALL|re.MULTILINE)

            diffs = difflib.unified_diff(self.last_content.splitlines(), content.splitlines())

            diff_content = ''

            for diff in diffs:
                diff_content += (diff + '\n')

            if diff_content != '' and len(diff_content) > self.change_size:
                self.last_content = content

                send_to = settings.SIMPLE_WEB_TOOLS_CONTENT_DESTINATION

                subject = '[%s] Updated: %s' % (settings.SIMPLE_WEB_TOOLS_CONTENT_PREFIX, self.title)

                send_mail(subject, diff_content, settings.ADMINS[0][1], [send_to], fail_silently=False)
                message = 'Successfully parsed content for URL: %s' % self.url
                logger.info(message)
            else:
                message = 'No significant changes observed for URL: %s' % self.url
                logger.info(message)
        else:
            if self.ignore_http_errors is False:
                message = 'Unable to parse URL: %s -  %s' % (self.url, status_code)
                logger.error(message)
                logger.error(content)

        self.last_check = timezone.now()
        self.save()

        return message

class RssFeed(models.Model):
    class Meta: # pylint: disable=too-few-public-methods, old-style-class, no-init
        verbose_name = 'RSS feed'
        verbose_name_plural = 'RSS feeds'

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
    class Meta: # pylint: disable=too-few-public-methods, old-style-class, no-init
        verbose_name = 'RSS feed item'
        verbose_name_plural = 'RSS feed items'

    objects = models.Manager()

    feed = models.ForeignKey(RssFeed, related_name='items', on_delete=models.CASCADE)

    title = models.CharField(max_length=1024)
    url = models.URLField(max_length=1024)
    content = models.TextField(max_length=1048576, null=True, blank=True)

    date = models.DateTimeField()
