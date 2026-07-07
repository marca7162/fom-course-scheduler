from typing import Dict, List, FrozenSet, Tuple
from .models import Course
import itertools

DAY_GROUPS = {
    "M": ("M",),
    "T": ("T",),
    "W": ("W",),
    "TH": ("TH",),
    "MW": ("M", "W"),
    "TTH": ("T", "TH"),
    "TH": ("TH",),
    "ALL": ("M", "T", "W", "TH"),
}


def generate_options_for_row(row: Dict) -> List[FrozenSet[Tuple[str, int]]]:
    day_group = row["day_group"].strip()
    days = DAY_GROUPS.get(day_group, (day_group,))
    periods = [
        int(p.strip())
        for p in row["period_options"].split(",")
        if p.strip().isdigit()
    ]
    pref = row["preference"].strip()
    weekly = (
        int(row.get("weekly_meeting", 0))
        if row.get("weekly_meeting", "").strip()
        else None
    )

    options = []
    if pref == "once_per_week" or weekly == 1:
        for d in days:
            for p in periods:
                options.append(frozenset([(d, p)]))
    elif pref == "two_in_row" or (weekly == 2 and len(days) == 1):
        if len(days) == 1:
            d = days[0]
            for i in range(len(periods) - 1):
                p1, p2 = periods[i], periods[i + 1]
                if p2 == p1 + 1:
                    options.append(frozenset([(d, p1), (d, p2)]))
    else:
        for p in periods:
            options.append(frozenset((d, p) for d in days))
    return options


def build_domains(
    avail_data: Dict[str, List[Dict]],
) -> Dict[str, List[FrozenSet[Tuple[str, int]]]]:
    domains = {}
    for course, rows in avail_data.items():
        has_room_pref = any(
            row["preference"] in ("classroom", "museum") for row in rows
        )
        if has_room_pref:
            # Combine rows via Cartesian product
            row_options_list = []
            for row in rows:
                opts = generate_options_for_row(row)
                if not opts:
                    row_options_list = []
                    break
                row_options_list.append(opts)
            if not row_options_list:
                domains[course] = []
                continue
            domain_set = set()
            for combo in itertools.product(*row_options_list):
                merged = set()
                for pat in combo:
                    merged.update(pat)
                domain_set.add(frozenset(merged))
            domains[course] = list(domain_set)
        else:
            # Take union of options from all rows
            domain_set = set()
            for row in rows:
                opts = generate_options_for_row(row)
                domain_set.update(opts)
            domains[course] = list(domain_set)
    return domains
