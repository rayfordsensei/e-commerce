from dataclasses import dataclass


@dataclass(slots=True)
class BaseUseCase[RepoT]:
    _repo: RepoT
