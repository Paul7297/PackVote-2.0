from enum import Enum


class TripStatus(str, Enum):
    PLANNING = "planning"
    VOTING = "voting"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"


class MemberRole(str, Enum):
    ORGANIZER = "organizer"
    MEMBER = "member"


class MemberStatus(str, Enum):
    INVITED = "invited"
    JOINED = "joined"
    DECLINED = "declined"
    LEFT = "left"