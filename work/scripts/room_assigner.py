from collections import defaultdict
from typing import Dict, List, Tuple, FrozenSet
from .models import Course, Room

def assign_rooms_backtracking(
    schedule: Dict[str, FrozenSet[Tuple[str, int]]],
    courses: List[Course],
    rooms: Dict[str, Room]
) -> Dict[str, Tuple[FrozenSet[Tuple[str, int]], str]]:
    items = []
    for course in courses:
        code = course.code
        pattern = schedule[code]
        needed = len(course.students)
        items.append((code, pattern, needed))

    items.sort(key=lambda x: (-len(x[1]), -x[2]))
    room_list = list(rooms.values())
    occupancy = defaultdict(set)  # (day, period) -> set of occupied room numbers
    assignment = {}

    def backtrack(idx: int) -> bool:
        if idx == len(items):
            return True
        code, pattern, needed = items[idx]
        candidates = []
        for room in room_list:
            if room.capacity < needed:
                continue
            free = True
            for slot in pattern:
                if slot in occupancy and room.number in occupancy[slot]:
                    free = False
                    break
            if free:
                candidates.append(room.number)

        for room_num in candidates:
            assignment[code] = room_num
            for slot in pattern:
                occupancy[slot].add(room_num)
            if backtrack(idx + 1):
                return True
            for slot in pattern:
                occupancy[slot].remove(room_num)
            del assignment[code]
        return False

    if backtrack(0):
        result = {}
        for course in courses:
            code = course.code
            pattern = schedule[code]
            room = assignment[code]
            result[code] = (pattern, room)
        return result
    else:
        raise RuntimeError("No feasible room assignment found.")