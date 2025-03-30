from typing import TYPE_CHECKING

import falcon
from falcon.app import App

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session

from db import get_db
from models import User


class UserResource:
    def on_get(self, req, resp) -> None:
        db: Session = next(get_db())
        users: list[User] = db.query(User).all()
        resp.media = [{"id": u.id, "username": u.username, "email": u.email} for u in users]


app: App = falcon.App()
app.add_route(uri_template="/users", resource=UserResource())
