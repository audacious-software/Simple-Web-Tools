
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache

from .models import UrlContentTracker

@never_cache
@staff_member_required
def simple_web_tools_url_update(request, tracker_id):
    tracker = get_object_or_404(UrlContentTracker, pk=tracker_id)

    if request.method == 'POST':
        content = request.POST.get('content', None)

        if content is not None and len(content) > 0:
            message = tracker.do_check(content)
        else:
            message = 'No content provided.'

        return JsonResponse({ 'message': message })

    context = {
        'tracker': tracker
    }

    return render(request, 'simple_web_tools_url_update.html', context=context)
