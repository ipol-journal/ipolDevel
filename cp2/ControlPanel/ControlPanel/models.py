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
    new_editor = instance
    # no email means nothing to look for in demoinfo
    if not new_editor.email:
        return

    # User stored in django DB.
    old_editor = usera.objects.get(pk=new_editor.pk)
    if not old_editor.email:
        add_editor(f"{new_editor.first_name} {new_editor.last_name}", new_editor.email)
        return

    settings = {"email": new_editor.email}
    demoinfo_editor, _ = api_post("/api/demoinfo/get_editor", "post", data=settings)
    new_editor_exists = demoinfo_editor.get("editor", None)

    settings = {"email": old_editor.email}
    demoinfo_editor, _ = api_post("/api/demoinfo/get_editor", "post", data=settings)
    old_editor_exists = demoinfo_editor.get("editor", None)

    # Same email means no change to make
    if old_editor.email == new_editor.email:
        return
    # new email not in demoinfo and an editor existed before with an email -> Update editor
    if not new_editor_exists and old_editor_exists:
        update_editor(
            f"{new_editor.first_name} {new_editor.last_name}",
            new_editor.email,
            old_editor.email,
        )
    # new email exists in demoinfo and different from CP -> email in use.
    # Possible missmatch in demoinfo, needs admin intervention.
    elif new_editor_exists and old_editor_exists:
        error = f"Failed to add editor '{new_editor.first_name} {new_editor.last_name}' with email '{new_editor.email}'. Already in use?"
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


def add_editor(name: str, email: str):
    settings = {
        "name": name,
        "mail": email,
    }
    response, _ = api_post("/api/demoinfo/add_editor", "post", data=settings)

    if response.get("status") != "OK":
        error = "Error, user tried to set up an email which is already in use."
        logger.error(error)
        raise ValidationError(error)
    else:
        logger.info("New editor added to demoinfo")
        return


def update_editor(username, email, old_email):
    settings = {
        "name": username,
        "old_email": old_email,
        "new_email": email,
    }
    update_response, _ = api_post(
        "/api/demoinfo/update_editor_email", "post", data=settings
    )

    if update_response.get("status") != "OK":
        logger.error(
            f"Could not update email of user '{username}', '{old_email}' --> '{email}'"
        )
