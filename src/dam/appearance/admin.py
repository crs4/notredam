from django.contrib import admin
from dam.appearance.models import Theme
#from settings import THEMES_PATH
import os
from django.http import HttpResponse
from django.utils import simplejson


class ThemeAdmin(admin.ModelAdmin):

    fields = ('name', 'css_file','description', 'SetAsCurrent')

    def save_model(self, request, obj, form, change):
        obj.save()
        if request.POST.has_key('SetAsCurrent'):
            theme_list = Theme.objects.all()
            for theme in theme_list:
                if theme.name != obj.name and theme.SetAsCurrent == True:
                    theme.SetAsCurrent = False
                    theme.save()
                    print 'in theme admin I changed theme ', theme.name,
            print 'Saved. Current theme is: ', obj.name

admin.site.register(Theme, ThemeAdmin)
