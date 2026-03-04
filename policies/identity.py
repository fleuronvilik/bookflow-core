from dataclasses import dataclass
from enum import Enum


class Forbidden(Exception):
    """Raised when an actor is not allowed to perform an action."""
    pass


class InvalidActor(Exception):
    """Raised when the actor context is internally inconsistent."""
    pass

class Role(str, Enum):
    ADMIN = "ADMIN"
    PARTNER = "PARTNER"


@dataclass(frozen=True)
class Actor:
    role: Role
    partner_id: str | None = None

    def __post_init__(self) -> None:
    # Invariant: a PARTNER must be bound to exactly one partner_id.
        if self.role is Role.PARTNER:
            if not self.partner_id:
                raise InvalidActor("PARTNER actor requires partner_id")

        # Invariant: an ADMIN is not a partner-scoped actor (keep scope explicit in use-cases).
        if self.role is Role.ADMIN:
            if self.partner_id:
                raise InvalidActor("ADMIN actor must not have partner_id")
