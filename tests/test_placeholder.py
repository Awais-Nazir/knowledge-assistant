def test_app_imports():
    """Placeholder test — verifies basic imports work."""
    from app.core.config import settings

    assert settings.APP_NAME == "Knowledge Assistant"


def test_security_functions():
    """Verifies password hashing works."""
    from app.core.security import hash_password, verify_password

    hashed = hash_password("TestPassword1")
    assert verify_password("TestPassword1", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_custom_exceptions():
    """Verifies exception hierarchy is correct."""
    from app.core.exceptions import (
        AppException,
        AuthenticationError,
        NotFoundError,
    )

    auth_err = AuthenticationError()
    assert auth_err.status_code == 401
    assert isinstance(auth_err, AppException)

    not_found = NotFoundError("User", "abc-123")
    assert not_found.status_code == 404
    assert "abc-123" in not_found.message
