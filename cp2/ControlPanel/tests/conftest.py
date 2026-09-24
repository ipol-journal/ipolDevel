"""Pytest fixtures for ControlPanel test suite."""
from contextlib import contextmanager

import pytest
import responses


@pytest.fixture
def mocked_responses():
    """Context-managed responses mock that intercepts all outgoing requests."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


@contextmanager
def mute_user_signals():
    """Disconnect pre_save and post_delete signals on User model."""
    from django.contrib.auth.models import User
    from django.db.models.signals import post_delete, pre_save

    from ControlPanel.models import delete_profile, user_created_handler

    pre_save.disconnect(user_created_handler, sender=User)
    post_delete.disconnect(delete_profile, sender=User)
    try:
        yield
    finally:
        pre_save.connect(user_created_handler, sender=User)
        post_delete.connect(delete_profile, sender=User)


@pytest.fixture
def user_factory(db):
    """Factory fixture to create users safely without firing demoinfo signals."""
    from django.contrib.auth.models import User

    def _create_user(
        username="testuser",
        email="testuser@example.com",
        password="password123",
        **kwargs,
    ):
        with mute_user_signals():
            return User.objects.create_user(
                username=username,
                email=email,
                password=password,
                **kwargs,
            )

    return _create_user


@pytest.fixture
def test_user(user_factory):
    """Default non-staff test user."""
    return user_factory()


@pytest.fixture
def staff_user(user_factory):
    """Staff test user."""
    return user_factory(username="staffuser", email="staff@example.com", is_staff=True)


@pytest.fixture
def auth_client(client, test_user):
    """Django test client pre-authenticated with test_user."""
    client.force_login(test_user)
    return client
