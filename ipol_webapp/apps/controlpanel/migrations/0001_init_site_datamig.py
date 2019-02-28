# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from ipol_webapp.settings import INSTALLED_APPS


def forward(apps, schema_editor):
    print("Forward Datamigration for site")
    if not schema_editor.connection.alias == 'default':
        return
    # if not apps.ready:
    #                       apps.populate(INSTALLED_APPS)
    #
    # if apps.is_installed('allauth'):
    #       print "allauth yes"
    #       print apps.get_app_config('allauth')


    if apps.ready:
        print "apps yes"

    if apps.is_installed('sites'):
        print "sites app installed"
        site = apps.get_model('sites.Site')


    s = site()
    s.pk=2
    s.domain='127.0.0.1:8000'
    s.name='localhost'
    s.save()

    s = site()
    s.pk=3
    s.domain='ipolcore.ipol.im'
    s.name='ipolcore.ipol.im'
    s.save()




def revert(apps, schema_editor):
    #"BORRA TODAS LAS FOTOS Y LAS GALERIAS"
    """revert back deleting the votes for a choice and adding it as a vote in the field"""
    print("Revers Datamigration for site")
    site = apps.get_model('sites', 'Site')
    for s in site.objects.filter(pk__gte=2):
        s.delete()




class Migration(migrations.Migration):

    dependencies = [
            ('sites', '0001_initial'),
    ]

    operations = [
            migrations.RunPython(forward,reverse_code=revert),
    ]
