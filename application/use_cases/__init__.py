from typing import Generic, TypeVar

T = TypeVar("T")


class BaseUseCase(Generic[T]):
    def __init__(self, repo: T):
        self._repo = repo
