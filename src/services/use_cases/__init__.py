from typing import TypeVar

RepoT = TypeVar("RepoT")


class BaseUseCase[RepoT]:  # noqa: B903  # It's not a value container!
    __slots__: tuple[str, ...] = ("_repo",)
    _repo: RepoT

    def __init__(self, repo: RepoT):
        self._repo = repo
