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
        pattern = schedule[code]
        needed = len(course.students)
        items.append((code, pattern, needed))

    items.sort(key=lambda x: (-len(x[1]), -x[2]))
    room_list = list(rooms.values())
    occupancy = init.defaultdict(set)
    assignment = {}
    call_count = [0]
    max_calls = 500000

    def backtrack(idx: int) -> bool:
        call_count[0] += 1
        
        # Fail fast if too many iterations
        if call_count[0] > max_calls:
            print(f"  Backtracking exceeded {max_calls} calls, returning False")
            return False
        
        if call_count[0] % 50000 == 0:
            print(f"  [Progress: {call_count[0]} calls, at idx {idx}/{len(items)}]")
        
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

        # Pruning: if no candidates, fail immediately
        if not candidates:
            return False
        
        # Heuristic: prefer rooms already occupied (to cluster)
        used_rooms = set()
        for slot in pattern:
            used_rooms.update(occupancy.get(slot, set()))
        candidates.sort(key=lambda r: (r not in used_rooms, r))
        
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
        raise RuntimeError(
            "No feasible room assignment found. Try adding more rooms or relaxing room capacity."
        )
