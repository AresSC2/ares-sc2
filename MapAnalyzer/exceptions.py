from typing import Tuple


class CustomDeprecationWarning(BaseException):
    def __init__(self, oldarg=None, newarg=None):
        self.old = oldarg
        self.new = newarg

    def __str__(self) -> str:
        return (
            f"[DeprecationWarning] Passing `{self.old}` argument is deprecated,"
            f" and will have no effect,\nUse `{self.new}` instead"
        )


class PatherNoPointsException(BaseException):
    def __init__(self, start, goal) -> None:
        super().__init__()
        self.start = start
        self.goal = goal

    def __str__(self) -> str:
        return (
            f"[PatherNoPointsException]"
            f"\nExpected: Start (pointlike), Goal (pointlike),"
            f"\nGot: Start {self.start}, Goal {self.goal}."
        )


class OutOfBoundsException(BaseException):
    def __init__(self, p: Tuple[int, int]) -> None:
        super().__init__()
        self.point = p

    def __str__(self) -> str:
        return f"[OutOfBoundsException]Point {self.point} is not inside the grid. No influence added."
