import logging

from django.conf import settings
from django.contrib.auth.models import User as usera
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, pre_save

# signals
from django.dispatch import receiver

from .utils import api_post

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

    # User stored in django DB.
    old_user = usera.objects.get(pk=instance.pk)
    # Same email means no change to make
    if old_user.email == instance.email:
        return

    settings = {"email": old_user.email}
    demoinfo_editor, _ = api_post("/api/demoinfo/get_editor", "post", data=settings)
    old_editor_exists = demoinfo_editor.get("editor", None)
    settings = {"email": instance.email}
    demoinfo_editor, _ = api_post("/api/demoinfo/get_editor", "post", data=settings)
    editor_exists = demoinfo_editor.get("editor", None)
    # there is an editor in demoinfo with same email as in django meaning it is an email change.
    if old_editor_exists and not editor_exists:
        settings = {
            "name": f"{instance.first_name} {instance.last_name}",
            "old_email": old_user.email,
            "new_email": instance.email,
        }
        update_response, _ = api_post(
            "/api/demoinfo/update_editor_email", "post", data=settings
        )

        if update_response.get("status") != "OK":
            error = update_response.get("error")
            logger.warning(f"User email could not be updated. {error}")
    # There is no editor in demoinfo or django with given email, create one in demoinfo
    elif not old_editor_exists and not editor_exists:
        settings = {
            "name": f"{instance.first_name} {instance.last_name}",
            "mail": instance.email,
        }
        response, response_code = api_post(
            "/api/demoinfo/add_editor", "post", data=settings
        )
        print(response, response_code)
    # error due to email being in use
    else:
        error = "Error, user tried to set up an email which is already in use."
        logger.error(error)
        raise ValidationError(error)


@receiver(post_delete, sender=User)
def delete_profile(sender, instance, *args, **kwargs):
    """
    Signal post-delete in djagno DB will try to remove the editor from demoinfo if it is found.
    """
    demoinfo_editor, _ = api_post(
        "/api/demoinfo/get_editor", "post", data={"email": instance.email}
    )
    editor_info = demoinfo_editor.get("editor", None)
    if editor_info:
        demoinfo_editor = api_post(
            "/api/demoinfo/remove_editor", "post", data={"editor_id": editor_info["id"]}
        )
        logger.info("User deleted.")
