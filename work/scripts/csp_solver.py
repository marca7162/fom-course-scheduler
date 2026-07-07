from collections import defaultdict
from typing import Dict, List, Optional, FrozenSet, Tuple, Set
from .models import Course

class CourseScheduler:
    def __init__(self, courses: List[Course], ignore_all_student_conflicts: bool = False):
        self.courses = courses
        self.course_dict = {c.code: c for c in courses}
        self.assignment = {}
        self.teacher_schedule = defaultdict(set)
        self.ignore_all_student_conflicts = ignore_all_student_conflicts

    @staticmethod
    def is_madr_course(code: str) -> bool:
        return code.startswith("MADR")

    def is_consistent(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> bool:
        course = self.course_dict[code]
        teacher = course.teacher

        # Teacher conflict
        for slot in pattern:
            if slot in self.teacher_schedule[teacher]:
                return False

        # Student conflict (only if both courses are MADR and not globally ignored)
        if not self.ignore_all_student_conflicts:
            for other_code, other_pattern in self.assignment.items():
                other_course = self.course_dict[other_code]
                if self.is_madr_course(code) and self.is_madr_course(other_code):
                    if course.students & other_course.students:
                        if pattern & other_pattern:
                            return False
        return True

    def assign(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> None:
        self.assignment[code] = pattern
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].add(slot)

    def unassign(self, code: str) -> None:
        pattern = self.assignment.pop(code)
        teacher = self.course_dict[code].teacher
        for slot in pattern:
            self.teacher_schedule[teacher].remove(slot)

    def count_forward_conflicts(self, code: str, pattern: FrozenSet[Tuple[str, int]]) -> int:
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
            # Student overlap potential (only for MADR)
            if not self.ignore_all_student_conflicts and self.is_madr_course(code) and self.is_madr_course(other.code):
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
        # MRV ordering
        self.courses.sort(key=lambda c: len(c.domain))
        if self.backtrack(0):
            return self.assignment
        return None