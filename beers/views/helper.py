"""Helper functions for checking the authentication status of requests"""

from django.http import HttpResponse

class HttpNotImplementedResponse(HttpResponse):
    status_code = 501


def is_authenticated_user_contest_runner(request):
    """
    Convenience method to check if the authenticated user is allowed to
    create contests
    """
    return (request.user.is_authenticated()
            and request.user.groups.filter(name='G_ContestRunner').count() > 0)


def is_authenticated_user_player(request):
    """
    Convenience method to check if the authenticated user is allowed to
    create contests
    """
    return (request.user.is_authenticated()
            and request.user.groups.filter(name='G_Player').count() > 0)
