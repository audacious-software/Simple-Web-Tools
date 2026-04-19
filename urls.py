# pylint: disable=line-too-long

import sys

if sys.version_info[0] > 2:
    from django.urls import re_path as url # pylint: disable=no-name-in-module
else:
    from django.conf.urls import url

from .views import simple_web_tools_url_update

urlpatterns = [
    url(r'^url-tracker/(?P<tracker_id>\d+)/manual-update$', simple_web_tools_url_update, name='simple_web_tools_url_update'),
]
