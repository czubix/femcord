from .dataclass import dataclass

from ..enums import EntitlementTypes
from ..utils import parse_time

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client
    from datetime import datetime

@dataclass
class Entitlement:
    __client: "Client" # type: ignore
    id: str
    sku_id: str
    application_id: str
    type: EntitlementTypes
    deleted: bool
    user_id: Optional[str] = None
    starts_at: Optional["datetime"] = None
    ends_at: Optional["datetime"] = None
    guild_id: Optional[str] = None
    consumed: Optional[bool] = None

    @classmethod
    def from_raw(cls, client: "Client", entitlement: dict) -> "Entitlement":
        if "starts_at" in entitlement and entitlement["starts_at"] is not None:
            entitlement["starts_at"] = parse_time(entitlement["starts_at"])

        if "ends_at" in entitlement and entitlement["ends_at"] is not None:
            entitlement["ends_at"] = parse_time(entitlement["ends_at"])

        return cls(client, **entitlement)

