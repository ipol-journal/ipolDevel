from django.conf import settings
from django.db import models
from django.contrib.auth.models import User as usera
from django.shortcuts import HttpResponseRedirect
from .utils import api_post

import logging

#signals
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_delete

User = settings.AUTH_USER_MODEL
logger = logging.getLogger(__name__)

@receiver(pre_save, sender=User)
def user_created_handler(sender, instance, *args, **kwargs):
    """
    Signal pre-save in djagno DB will try to update the editor with given email if it exists.
    """
    # no email means nothing to look for in demoinfo
    if not instance.email:
        return

    old_user = usera.objects.get(pk=instance.pk)
    # Same email means no change to make
    if old_user.email == instance.email:
        return

    demoinfo_editor = api_post('/api/demoinfo/get_editor', {'email': old_user.email})
    old_editor_exists = demoinfo_editor['editor']
    demoinfo_editor = api_post('/api/demoinfo/get_editor', {'email': instance.email})
    editor_exists = demoinfo_editor['editor']
    if old_editor_exists and not editor_exists:
        settings = {
            'name': f'{instance.first_name} {instance.last_name}',
            'old_email': old_user.email,
            'new_email': instance.email
        }
        update_response = api_post('/api/demoinfo/update_editor_email', settings)

        if update_response.get('status') != 'OK':
            error = update_response.get('error')
            logger.warning(f'User email could not be updated. {error}')
    elif not old_editor_exists and not editor_exists:
        settings = {
            'name': f'{instance.first_name} {instance.last_name}',
            'mail': instance.email
        }
        response = api_post('/api/demoinfo/add_editor', settings)
    else:
        logger.error('Error, user tried to set up an email which is already in use.')
        raise Exception('Error, tried to set up an email which is already in use.')

@receiver(post_delete, sender=User)
def delete_profile(sender,instance,*args,**kwargs):
    """
    Signal post-delete in djagno DB will try to remove the editor from demoinfo if it is found.
    """
    demoinfo_editor = api_post('/api/demoinfo/get_editor', {'email': instance.email})
    editor_info = demoinfo_editor['editor']
    if editor_info:
        demoinfo_editor = api_post('/api/demoinfo/remove_editor', {'editor_id': editor_info['id']})
        logger.info('User deleted.')