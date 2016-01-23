from django.http import HttpResponse

class HttpNotImplementedResponse(HttpResponse):
	status_code = 501

def is_authenticated_user_contest_runner(request):
	"""Convenience method to check if the authenticated user is allowed to
	create contests"""
	return (request.user.is_authenticated()
		and len([g for g in request.user.groups.all() if g.name == 'G_ContestRunner']) > 0)

def is_authenticated_user_player(request):
	"""Convenience method to check if the authenticated user is allowed to
	create contests"""
	return (request.user.is_authenticated()
		and len([g for g in request.user.groups.all() if g.name == 'G_Player']) > 0)
