import falcon


def assert_owner(resource_owner_id: int, acting_user_id: int) -> None:
    """Raise 403 unless the caller owns the resource."""  # noqa: DOC501
    if resource_owner_id != acting_user_id:
        raise falcon.HTTPForbidden(
            title="Forbidden",
            description="You do not have permission to access this resource.",
        )
