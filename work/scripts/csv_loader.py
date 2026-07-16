import csv
from collections import defaultdict
from typing import Dict, Set, List
from .models import Course, Room


def read_rooms(csv_path: str) -> Dict[str, "Room"]:
    from .models import Room

    rooms = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rooms[row["Room Number"]] = Room(
                number=row["Room Number"],
                capacity=int(row["Capacity"]),
                av1=row["Av1"].strip() == "0",
                av2=row["Av2"].strip() == "0",
                av3=row["Av3"].strip() == "0",
                av4=row["Av4"].strip() == "0",
                av5=row["Av5"].strip() == "0",
                av6=row["Av6"].strip() == "0",
                av7=row["Av7"].strip() == "0",
            )

    return rooms


def read_enrollment(csv_path: str) -> Dict[str, Set[int]]:
    enroll = defaultdict(set)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            enroll[row["course_id"]].add(int(row["student_id"]))
    return enroll


def read_availability(csv_path: str) -> Dict[str, List[Dict]]:
    avail = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            avail[row["course_id"]].append(row)
    return avail


def build_course_objects(
    avail_data: Dict, enroll_data: Dict, teacher_of: Dict, domains: Dict
) -> List[Course]:
    from .domain_builder import build_domains

    courses = []
    for code, domain in domains.items():
        if not domain:
            continue
        teacher = teacher_of.get(code, "Unknown")
        first_row = avail_data[code][0]
        pref = first_row["preference"].strip()
        weekly_str = first_row.get("weekly_meeting", "").strip()
        weekly = int(weekly_str) if weekly_str else None
        room_pref = None
        for row in avail_data[code]:
            if row["preference"] in ("classroom", "museum"):
                room_pref = row["preference"]
        students = enroll_data.get(code, set())
        courses.append(
            Course(
                code=code,
                teacher=teacher,
                students=students,
                domain=domain,
                preference=pref,
                weekly_meeting=weekly,
                room_preference=room_pref,
            )
        )
    return courses
