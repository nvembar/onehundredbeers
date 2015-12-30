from django.contrib import admin
from .models import Contest
from .models import Beer
from .models import Player
from .models import Contest_Beer
from .models import Contest_Player
from .models import Checkin
from .models import Unvalidated_Checkin

# Register your models here.
admin.site.register(Contest)
admin.site.register(Beer)
admin.site.register(Player)
admin.site.register(Contest_Beer)
admin.site.register(Contest_Player)
admin.site.register(Checkin)
admin.site.register(Unvalidated_Checkin)
