from app.models import User
import pytest


def test_validate_password():
    assert User.validate_password("ValidPass1!") is True
    assert not User.validate_password("short")
    assert not User.validate_password("noupper1!")
    assert not User.validate_password("NOLOWER1!")
    assert not User.validate_password("NoNumber!")
    assert not User.validate_password("NoSpecial1")


def test_set_and_check_password():
    user = User(name="n", email="e", role="r")
    user.set_password("ValidPass1!")
    assert user.check_password("ValidPass1!")
    with pytest.raises(ValueError):
        user.set_password("bad")
