import logging
from django.shortcuts import get_object_or_404, render
from django.db import transaction
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from beers.models import Player, Contest_Player
from beers.forms.registration import RegistrationForm, ProfileForm

logger = logging.getLogger(__name__)


@transaction.atomic
def signup(request):
    f = None
    if request.method == 'POST':
        f = RegistrationForm(request.POST)
        if f.is_valid():
            # Create a new User and Player object
            data = f.clean()
            user = User.objects.create_user(data.get('username'),
                                            email=data.get('email'),
                                            first_name=data.get('first_name'),
                                            last_name=data.get('last_name'),
                                            password=data.get('password'))
            # Making an assumption that G_Player exists
            user.groups.add(Group.objects.get(name='G_Player'))
            user.save()
            player = Player.objects.create_player(user,
                                                  personal_statement=data.get('personal_statement'),
                                                  untappd_rss=data.get('untappd_rss'),
                                                  untappd_username=data.get('untappd_username'))
            player.save()
            return render(request, 'registration/signup_success.html')
    else:
        f = RegistrationForm()
    return render(request, 'registration/signup.html', {'form': f})

@login_required
@transaction.atomic
def update_profile(request):
    if not request.user.is_authenticated:
        raise PermissionDenied("User {} is not authenticated".format(request.username))
    player = get_object_or_404(Player.objects, user_id=request.user.id)
    f = None
    update_success = False
    data = {'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'personal_statement': player.personal_statement,
            'untappd_rss': player.untappd_rss,
            'untappd_username': player.untappd_username}
    if request.method == 'GET':
        f = ProfileForm(data)
    elif request.method == 'POST':
        f = ProfileForm(request.POST, initial=data)
        if f.is_valid() and f.has_changed():
            changed_data = f.changed_data
            data = f.clean()
            if ('first_name' in changed_data or
                    'last_name' in changed_data or
                    'email' in changed_data):
                request.user.first_name = data.get('first_name')
                request.user.last_name = data.get('last_name')
                request.user.email = data.get('email')
                request.user.save()
            if ('personal_statement' in changed_data or
                    'untappd_rss' in changed_data or
                    'untappd_username' in changed_data):
                player.personal_statement = data.get('personal_statement')
                player.untappd_rss = data.get('untappd_rss')
                player.untappd_username = data.get('untappd_username')
                player.save()
            if 'untappd_rss' in changed_data:
                cps = Contest_Player.objects.filter(player_id=player.id)
                # If the RSS feed changes, reset the last load to the beginning
                # of the contest
                for cp in cps:
                    cp.last_checkin_load = cp.contest.start_date
                    cp.save()
            update_success = True
    # This will include errors if necessary
    return render(request, 'registration/profile.html',
                  {'form': f,
                   'user': request.user,
                   'player': player,
                   'success': update_success})
