"""
Bridge between the `users` table (application accounts) and `auth_users`
(the table `farms.user_id` actually references).

`farms.user_id` has a foreign key to `auth_users.id`, so a farmer who signed up
through `users` needs a matching `auth_users` row before any farm can be saved.

The subtlety is that `auth_users` puts UNIQUE indexes on farmer_id, email,
username and phone, while `users` only constrains email and username. Mirroring
a user across naively therefore raises

    psycopg2.errors.UniqueViolation: duplicate key value violates unique
    constraint "ix_auth_users_phone"

whenever two farmers share a phone number, or a stale auth_users row already
holds one of these values — and because the farm write happens in the same
transaction, the farmer's entire profile save fails with a 500.

This helper creates the link row defensively: anything that would collide on a
unique index is dropped rather than failing the save. Only `id` actually
matters for the foreign key; the mirrored contact fields are convenience.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def ensure_auth_user(db: Session, user) -> Optional[object]:
    """
    Make sure an `auth_users` row exists with the same id as `user`.

    Returns the row, or None when `user` is falsy. Never raises for a unique
    collision on a mirrored field.
    """
    from farmxpert.models.user_models import AuthUser

    if user is None:
        return None

    existing = db.query(AuthUser).filter(AuthUser.id == user.id).first()
    if existing:
        return existing

    farmer_id = "FRM%04d" % user.id
    email = user.email
    username = user.username
    phone = getattr(user, "phone", None)

    # Drop any value already claimed by a different auth_users row. These are
    # informational copies; the id is what the foreign key needs.
    for field, value in (("farmer_id", farmer_id), ("email", email),
                         ("username", username), ("phone", phone)):
        if not value:
            continue
        clash = (
            db.query(AuthUser)
            .filter(getattr(AuthUser, field) == value, AuthUser.id != user.id)
            .first()
        )
        if not clash:
            continue
        logger.info(
            "auth_users.%s=%r already belongs to id=%s; linking user id=%s without it",
            field, value, clash.id, user.id,
        )
        if field == "farmer_id":
            farmer_id = "FRM%04d-%s" % (user.id, user.id)
        elif field == "email":
            email = None
        elif field == "username":
            username = None
        elif field == "phone":
            phone = None

    # email and username are NOT NULL on auth_users, so fall back to a value
    # that is unique by construction rather than leaving them empty.
    if not email:
        email = "user%s@farms.local" % user.id
    if not username:
        username = "user%s" % user.id

    auth_user = AuthUser(
        id=user.id,
        farmer_id=farmer_id,
        email=email,
        username=username,
        name=getattr(user, "full_name", None) or user.username,
        phone=phone,
        password_hash=user.hashed_password,
        role=getattr(user, "role", "farmer"),
    )
    db.add(auth_user)
    db.flush()
    return auth_user
