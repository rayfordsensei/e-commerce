import abc


class AbstractTokenIssuer(abc.ABC):
    """Generate a short-lived JWT for a given user id."""

    @abc.abstractmethod
    def issue(self, user_id: int) -> str:
        pass


class AbstractTokenVerifier(abc.ABC):
    """Validate an incoming JWT and return the 'sub' claim."""

    @abc.abstractmethod
    def verify(self, token: str) -> int:
        pass
