import sqlite3
from pathlib import Path
from typing import Optional, List
from collections import defaultdict

from .csv_loader import read_rooms, read_enrollment, read_availability, build_course_objects
from .domain_builder import build_domains
from .csp_solver import CourseScheduler
from .room_assigner import assign_rooms_backtracking
from .csv_exporter import write_course_room_schedule, write_teacher_schedule, write_student_schedule


def _build_course_rows(room_schedule: dict) -> list:
    rows = []
    for code, (pattern, room) in room_schedule.items():
        for day, period in sorted(pattern):
            rows.append(
                {
                    "courseCode": code,
                    "day": day,
                    "period": period,
                    "roomNumber": room,
                }
            )
    return rows


def _count_conflicts(room_schedule: dict, enroll_data: dict) -> int:
    course_slots = {
        code: {(day, period) for day, period in sorted(pattern)}
        for code, (pattern, _) in room_schedule.items()
    }

    conflicts = 0
    course_codes = list(room_schedule.keys())
    for i in range(len(course_codes)):
        for j in range(i + 1, len(course_codes)):
            first = course_codes[i]
            second = course_codes[j]
            shared_students = enroll_data.get(first, set()) & enroll_data.get(
                second, set()
            )
            if not shared_students:
                continue
            overlap = course_slots[first] & course_slots[second]
            if overlap:
                conflicts += len(overlap)
    return conflicts


def _build_candidate(
    name: str,
    courses: List,
    rooms_data: dict,
    enroll_data: dict,
    ignore_student_conflicts: bool,
    order_key,
) -> Optional[dict]:
    scheduler = CourseScheduler(
        list(courses),
        ignore_all_student_conflicts=ignore_student_conflicts,
        order_key=order_key,
    )
    assignment = scheduler.solve()
    if assignment is None:
        return None

    room_schedule = assign_rooms_backtracking(assignment, courses, rooms_data)
    rows = _build_course_rows(room_schedule)
    return {
        "id": name.lower().replace(" ", "-"),
        "name": name,
        "conflictCount": _count_conflicts(room_schedule, enroll_data),
        "rows": rows,
        "roomSchedule": room_schedule,
    }


def run_scheduler(
    rooms_path: str,
    enroll_path: str,
    avail_path: str,
    output_dir: Optional[str] = None,
) -> dict:
    """Organize the entire scheduling pipeline and return candidate schedules."""
    rooms_data = read_rooms(rooms_path)
    enroll_data = read_enrollment(enroll_path)
    avail_data = read_availability(avail_path)

    domains = build_domains(avail_data)

    teacher_of = {}
    for code, rows in avail_data.items():
        teacher_of[code] = rows[0]["teacher_name"]

    courses = build_course_objects(avail_data, enroll_data, teacher_of, domains)
    if not courses:
        raise RuntimeError("No schedulable courses found.")

    candidate_specs = [
        ("Balanced", False, lambda c: (len(c.domain), len(c.students))),
        ("Student-first", False, lambda c: (len(c.domain), -len(c.students))),
        ("Relaxed", True, lambda c: (len(c.domain), len(c.students))),
    ]

    candidates = []
    for name, ignore_conflicts, order_key in candidate_specs:
        scheduler = CourseScheduler(
            list(courses),
            ignore_all_student_conflicts=ignore_conflicts,
            order_key=order_key,
        )
        assignment = scheduler.solve()
        if assignment is None:
            continue

        room_schedule = assign_rooms_backtracking(
            assignment, courses, rooms_data
        )
        rows = _build_course_rows(room_schedule)
        candidates.append(
            {
                "id": name.lower().replace(" ", "-"),
                "name": name,
                "conflictCount": _count_conflicts(room_schedule, enroll_data),
                "rows": rows,
                "roomSchedule": room_schedule,
            }
        )

    if not candidates:
        raise RuntimeError("No feasible schedule could be generated.")

    candidates.sort(key=lambda item: (item["conflictCount"], item["name"]))
    best_candidate = candidates[0]
    room_schedule = best_candidate["roomSchedule"]

    course_room_list = []
    teacher_list = []
    student_list = []

    course_teacher = {c.code: c.teacher for c in courses}

    for code, (pattern, room) in room_schedule.items():
        for day, period in sorted(pattern):
            course_room_list.append(
                {
                    "courseCode": code,
                    "day": day,
                    "period": period,
                    "roomNumber": room,
                }
            )
            teacher_list.append(
                {
                    "teacherName": course_teacher.get(code, "Unknown"),
                    "day": day,
                    "period": period,
                    "courseCode": code,
                    "roomNumber": room,
                }
            )

    student_courses = defaultdict(list)
    for course, students in enroll_data.items():
        for sid in students:
            student_courses[sid].append(course)

    for sid, courses_list in student_courses.items():
        for cid in courses_list:
            if cid in room_schedule:
                pattern, room = room_schedule[cid]
                for day, period in sorted(pattern):
                    student_list.append(
                        {
                            "studentId": sid,
                            "courseCode": cid,
                            "day": day,
                            "period": period,
                            "roomNumber": room,
                        }
                    )

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        write_course_room_schedule(room_schedule, output_path / "course_room_schedule.csv")
        write_teacher_schedule(room_schedule, courses, output_path / "teacher_schedule.csv")
        write_student_schedule(student_list, output_path / "student_schedule.csv")

    return {
        "course_room": course_room_list,
        "teacher": teacher_list,
        "student": student_list,
        "selectedSchedule": course_room_list,
        "selectedCandidateId": best_candidate["id"],
        "selectedConflictCount": best_candidate["conflictCount"],
        "candidates": [
            {
                "id": candidate["id"],
                "name": candidate["name"],
                "conflictCount": candidate["conflictCount"],
                "rows": candidate["rows"],
            }
            for candidate in candidates
        ],
    }