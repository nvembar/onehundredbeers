from django.contrib import admin
import beers.models as models

# Register your models here.
admin.site.register(models.Contest)
admin.site.register(models.Beer)
admin.site.register(models.Player)
admin.site.register(models.Contest_Beer)
admin.site.register(models.Contest_Player)
admin.site.register(models.Checkin)
admin.site.register(models.Unvalidated_Checkin)
admin.site.register(models.Brewery)
admin.site.register(models.Contest_Brewery)
