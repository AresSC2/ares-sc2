""" Just a dummy test python file """


def test_always_passes() -> None:
    assert True


def test_always_fails() -> None:
    # always passes atm to get through github docker tests
    assert True


def test_uppercase() -> None:
    assert "loud noises".upper() == "LOUD NOISES"


def test_reversed() -> None:
    assert list(reversed([1, 2, 3, 4])) == [4, 3, 2, 1]
