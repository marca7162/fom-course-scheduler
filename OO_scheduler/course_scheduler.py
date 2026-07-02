import initializer as init


# ---------- CSP Solver with conditional student conflicts ----------
class CourseScheduler:
    def __init__(
        self,
        courses: init.List[init.Course],
        ignore_all_student_conflicts: bool = False,
    ):
        self.courses = courses
        self.course_dict = {c.code: c for c in courses}
        self.assignment = {}
        self.teacher_schedule = init.defaultdict(set)
        self.ignore_all_student_conflicts = ignore_all_student_conflicts

    def is_madr_course(self, code: str) -> bool:
        return code.startswith("MADR")

    def is_consistent(
        self, code: str, pattern: init.FrozenSet[init.Tuple[str, int]]
    ) -> bool:
        course = self.course_dict[code]
        teacher = course.teacher

        # 1) Teacher conflict (always enforced)
        for slot in pattern:
            if slot in self.teacher_schedule[teacher]:
                return False

        # 2) Student conflict (only if both courses are MADR and not globally ignored)
        if not self.ignore_all_student_conflicts:
            for other_code, other_pattern in self.assignment.items():
                other_course = self.course_dict[other_code]
                # Apply student conflict only if both course codes start with "MADR"
                if self.is_madr_course(code) and self.is_madr_course(
                    other_code
                ):
                    if course.students & other_course.students:
                        if pattern & other_pattern:
                            return False
        return True

    def assign(
        self, code: str, pattern: init.FrozenSet[init.Tuple[str, int]]
    ) -> None:
        self.assignment[code] = pattern
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].add(slot)

    def unassign(self, code: str) -> None:
        pattern = self.assignment.pop(code)
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].remove(slot)

    def count_forward_conflicts(
        self, code: str, pattern: init.FrozenSet[init.Tuple[str, int]]
    ) -> int:
        conflicts = 0
        course = self.course_dict[code]
        for other in self.courses:
            if other.code == code or other.code in self.assignment:
                continue
            # Teacher overlap potential
            if other.teacher == course.teacher:
                for slot in pattern:
                    for dom in other.domain:
                        if slot in dom:
                            conflicts += 1
                            break
            # Student overlap potential only if both MADR
            if (
                not self.ignore_all_student_conflicts
                and self.is_madr_course(code)
                and self.is_madr_course(other.code)
            ):
                if course.students & other.students:
                    for slot in pattern:
                        for dom in other.domain:
                            if slot in dom:
                                conflicts += 1
                                break
        return conflicts

    def backtrack(self, idx: int) -> bool:
        if idx == len(self.courses):
            return True
        course = self.courses[idx]
        code = course.code
        domain_sorted = sorted(
            course.domain,
            key=lambda pat: self.count_forward_conflicts(code, pat),
        )
        for pattern in domain_sorted:
            if self.is_consistent(code, pattern):
                self.assign(code, pattern)
                if self.backtrack(idx + 1):
                    return True
                self.unassign(code)
        return False

    def solve(
        self,
    ) -> init.Optional[init.Dict[str, init.FrozenSet[init.Tuple[str, int]]]]:
        self.courses.sort(key=lambda c: len(c.domain))
        if self.backtrack(0):
            return self.assignment
        return None


# ---------- Room assignment with backtracking ----------
def assign_rooms_backtracking(
    schedule: init.Dict[str, init.FrozenSet[init.Tuple[str, int]]],
    courses: init.List[init.Course],
    rooms: init.Dict[str, init.Room],
) -> init.Dict[str, init.Tuple[init.FrozenSet[init.Tuple[str, int]], str]]:

    items = []
    for course in courses:
        code = course.code

        if code not in schedule:
            continue

        pattern = schedule[code]
        needed = len(course.students)
        items.append((code, pattern, needed))

    # Hardest courses first:
    # 1. bigger classes first
    # 2. more periods first
    items.sort(key=lambda x: (-x[2], -len(x[1])))

    # Smallest rooms first so we do not waste big rooms
    room_list = sorted(rooms.values(), key=lambda r: r.capacity)

    occupancy = init.defaultdict(set)
    assignment = {}

    def backtrack(idx: int) -> bool:
        if idx == len(items):
            return True

        code, pattern, needed = items[idx]

        candidates = []
        for room in room_list:
            if room.capacity < needed:
                continue

            room_available = True
            for slot in pattern:
                if room.number in occupancy[slot]:
                    room_available = False
                    break

            if room_available:
                candidates.append(room)

        if not candidates:
            return False

        for room in candidates:
            assignment[code] = room.number

            for slot in pattern:
                occupancy[slot].add(room.number)

            if backtrack(idx + 1):
                return True

            for slot in pattern:
                occupancy[slot].remove(room.number)

            del assignment[code]

        return False

    if not backtrack(0):
        raise RuntimeError(
            "No feasible room assignment found. Try adding more rooms or relaxing room capacity."
        )

    result = {}
    for code, pattern, needed in items:
        result[code] = (pattern, assignment[code])

    return result