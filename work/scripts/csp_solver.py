from collections import defaultdict
import random
from typing import Dict, List, Optional, FrozenSet, Tuple, Set
from .models import Course

class CourseScheduler:
    def __init__(
        self,
        courses: List[Course],
        ignore_all_student_conflicts: bool = False,
        order_key=None,
    ):
        self.courses = courses
        self.course_dict = {c.code: c for c in courses}
        self.assignment = {}
        self.teacher_schedule = defaultdict(set)
        self.ignore_all_student_conflicts = ignore_all_student_conflicts
        self.order_key = order_key or (lambda c: len(c.domain))

    @staticmethod
    def is_madr_course(code: str) -> bool:
        return code.startswith("MADR")

    @staticmethod
    def occupied_slots(course: Course, pattern: FrozenSet[Tuple[str, int]]) -> Set[Tuple[str, int]]:
        slots = set(pattern)
        if course.needs_extra_time:
            slots.update((day, period + 1) for day, period in pattern)
        return slots

    def is_consistent(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> bool:
        course = self.course_dict[code]
        teacher = course.teacher
        occupied = self.occupied_slots(course, pattern)

        # Teacher conflict
        for slot in occupied:
            if slot in self.teacher_schedule[teacher]:
                return False

        # Student conflict (only if both courses are MADR and not globally ignored)
        if not self.ignore_all_student_conflicts:
            for other_code, other_pattern in self.assignment.items():
                other_course = self.course_dict[other_code]
                if self.is_madr_course(code) and self.is_madr_course(other_code):
                    if course.students & other_course.students:
                        other_occupied = self.occupied_slots(other_course, other_pattern)
                        if occupied & other_occupied:
                            return False
        return True

    def assign(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> None:
        self.assignment[code] = pattern
        teacher = self.course_dict[code].teacher
        for slot in self.occupied_slots(self.course_dict[code], pattern):
            self.teacher_schedule[teacher].add(slot)

    def unassign(self, code: str) -> None:
        pattern = self.assignment.pop(code)
        teacher = self.course_dict[code].teacher
        for slot in self.occupied_slots(self.course_dict[code], pattern):
            self.teacher_schedule[teacher].remove(slot)

    def count_forward_conflicts(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> int:
        conflicts = 0
        course = self.course_dict[code]
        occupied = self.occupied_slots(course, pattern)
        for other in self.courses:
            if other.code == code or other.code in self.assignment:
                continue
            # Teacher overlap potential
            if other.teacher == course.teacher:
                for slot in occupied:
                    for dom in other.domain:
                        if slot in self.occupied_slots(other, dom):
                            conflicts += 1
                            break
            # Student overlap potential (only for MADR)
            if not self.ignore_all_student_conflicts and self.is_madr_course(code) and self.is_madr_course(other.code):
                if course.students & other.students:
                    for slot in occupied:
                        for dom in other.domain:
                            if slot in self.occupied_slots(other, dom):
                                conflicts += 1
                                break
        return conflicts

    def backtrack(self, idx: int) -> bool:
        if idx == len(self.courses):
            return True
        course = self.courses[idx]
        code = course.code
        # Randomize equally good period options so a comma-separated list such as
        # "1,2,3,4" does not always select the same period on every run.  Sorting
        # is stable, so the forward-conflict heuristic still takes priority.
        domain_options = list(course.domain)
        random.shuffle(domain_options)
        domain_sorted = sorted(
            domain_options,
            key=lambda pat: self.count_forward_conflicts(code, pat)
        )
        for pattern in domain_sorted:
            if self.is_consistent(code, pattern):
                self.assign(code, pattern)
                if self.backtrack(idx + 1):
                    return True
                self.unassign(code)
        return False

    def solve(self) -> Optional[Dict[str, FrozenSet[Tuple[str, int]]]]:
        self.courses.sort(key=self.order_key)
        if self.backtrack(0):
            return self.assignment
        return None
