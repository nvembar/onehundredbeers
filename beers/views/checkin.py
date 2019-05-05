from beers.models import Unvalidated_Checkin
from .helper import is_authenticated_user_contest_runner
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods


@login_required
@require_http_methods(['POST'])
def add_unvalidated_checkin(request, untappd_url):
    """
    Adds an unvalidated checkin by its Untappd URL
    """

    pass

