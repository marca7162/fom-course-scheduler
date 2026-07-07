from dataclasses import dataclass
from typing import Set, FrozenSet, Tuple, Optional, List


@dataclass
class Room:
    number: str
    capacity: int
    av1: bool
    av2: bool
    av3: bool
    av4: bool
    av5: bool
    av6: bool
    av7: bool


@dataclass
class Teacher:
    name: str
    # Possibly more fields later


@dataclass
class Student:
    id: int
    name: str = ""


@dataclass
class Course:
    code: str
    teacher: str  # teacher name
    students: Set[int]  # set of student IDs
    domain: List[FrozenSet[Tuple[str, int]]]  # possible time patterns
    preference: str
    weekly_meeting: Optional[int] = None
    room_preference: Optional[str] = None
