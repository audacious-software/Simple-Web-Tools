# pylint: disable=line-too-long

from django.urls import re_path

from .views import simple_web_tools_url_update

urlpatterns = [
    re_path(r'^url-tracker/(?P<tracker_id>\d+)/manual-update$', simple_web_tools_url_update, name='simple_web_tools_url_update'),
]
