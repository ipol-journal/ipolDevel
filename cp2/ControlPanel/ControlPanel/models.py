import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete, pre_save

# signals
from django.dispatch import receiver

from .utils import api_post

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=User)
def user_created_handler(sender, instance, *args, **kwargs):
    """
    Signal pre-save in djagno DB will try to update the editor with given email if it exists.
    """
    new_editor = instance
    # User stored in django DB.
    # no email means nothing to look for in demoinfo
    if not new_editor.email:
        old_editor = User.objects.filter(username=new_editor).first()
        # If old_editor isn't found it means it is a new editor right before the step
        # to set up email. Return allows to create user and wait
        # for email to be set
        if old_editor:
            error = "Please do not remove the email"
            raise ValidationError(error)
        return

    old_editor = User.objects.get(username=new_editor)
    logger.info(
        "old", old_editor, old_editor.email, old_editor.first_name, old_editor.last_name
    )
    logger.info(
        "new", new_editor, new_editor.email, new_editor.first_name, new_editor.last_name
    )

    # Same email means no change to make
    if new_editor and old_editor.email == new_editor.email:
        logger.info("Same email, nothing to do")
        return

    demoinfo_editor, _ = api_post(
        f"/api/demoinfo/editor?email={new_editor.email}", "get"
    )
    new_editor_exists = demoinfo_editor.get("editor", None)

    demoinfo_editor, _ = api_post(
        f"/api/demoinfo/editor?email={old_editor.email}", "get"
    )
    old_editor_exists = demoinfo_editor.get("editor", None)

    logger.info("old", old_editor_exists, "new", new_editor_exists)
    # new email not in demoinfo and an editor existed before with an email -> Update editor
    if not new_editor_exists and old_editor_exists:
        update_editor(
            f"{new_editor.first_name} {new_editor.last_name}",
            new_editor.email,
            old_editor.email,
        )
        return

    if not new_editor_exists:
        add_editor(f"{new_editor.first_name} {new_editor.last_name}", new_editor.email)
        return
    # new email exists in demoinfo and different from CP -> email in use.
    # Possible missmatch in demoinfo, needs admin intervention.
    error = f"Failed to add editor '{new_editor.first_name} {new_editor.last_name}' with email '{new_editor.email}'. Already in use?"
    logger.error(error)
    raise ValidationError(error)


@receiver(post_delete, sender=User)
def delete_profile(sender, instance, *args, **kwargs):
    """
    Signal post-delete in djagno DB will try to remove the editor from demoinfo if it is found.
    """
    demoinfo_editor, _ = api_post(
        "/api/demoinfo/editor", "get", params={"email": instance.email}
    )
    editor_info = demoinfo_editor.get("editor", None)
    editor_id = editor_info["id"]
    if editor_info:
        demoinfo_editor, status = api_post(
            f"/api/demoinfo/editor/{editor_id}", "delete"
        )
        if status != 204:
            error = demoinfo_editor.json()
            error_message = error.get("error")
            logger.error(f"User could not be deleted. {error_message}")

        logger.info("User deleted.")


def add_editor(name: str, email: str):
    data = {
        "name": name,
        "mail": email,
    }
    _, status = api_post("/api/demoinfo/editor", "post", params=data)

    if status != 201:
        error = "Error, user tried to set up an email which is already in use."
        logger.error(error)
        raise ValidationError(error)
    else:
        logger.info("New editor added to demoinfo")
        return


def update_editor(username, email, old_email):
    data = {
        "name": username,
        "old_email": old_email,
        "new_email": email,
    }
    _, status = api_post("/api/demoinfo/editor", "patch", params=data)

    if status != 201:
        error_message = (
            f"Could not update email of user '{username}', '{old_email}' --> '{email}'"
        )
        logger.error(error_message)
        raise ValidationError(error_message)
