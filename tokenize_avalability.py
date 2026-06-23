import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "clean_availability.csv"
OUTPUT_FILE = ROOT / "tokenized_availability.csv"


def clean_course_name(name):
    # course name clean
    if pd.isna(name):
        return ""

    return str(name).strip().title()


def normalize_text(text):
    # make everything uniform for tokenizing is done right
    if pd.isna(text):
        return ""

    return str(text).strip().lower()


def get_day_group(text):
    # T1
    text = normalize_text(text)

    if pd.isna(text):
        return ""

    if "m/w" in text or "mw" in text:
        return "MW"
    if "t/th" in text or "tth" in text:
        return "TTH"
    if "tuesday" in text or "tuesdays" in text:
        return "oneDay"
    if "thursday" in text or "thursdays" in text:
        return "oneDay"
    if "any time" in text or "anytime" in text:
        if "m/w" in text:
            return "MW"
        if "t/th" in text:
            return "TTH"
        return "anyDay"
    return "unknown"


def get_days(text):
    # T2
    text = normalize_text(text)

    if "m/w" in text or "mw" in text:
        return "M,W"
    if "t/th" in text or "tth" in text:
        return "T,TH"
    if "tuesday" in text or "tuesdays" in text:
        return "T"
    if "thursday" in text or "thursdays" in text:
        return "TH"
    if "any time" in text or "anytime" in text:
        return "M,T,W,TH"
    return ""


def get_period_type(text):
    # T3
    text = normalize_text(text)

    if not text:
        return ""
    if "whole" in text or "any time" in text or "anytime" in text:
        return "wholeDay"
    if "1st" in text or "first" in text:
        return "morning"
    if "2nd" in text or "second" in text:
        return "morning"
    if (
        "after 12" in text
        or "after 15" in text
        or "16:00" in text
        or "4pm" in text
        or "4 pm" in text
    ):
        return "evening"
    if re.search(r"9:30|10:30|11:00|12:20|13:50", text):
        return "morning"
    if re.search(r"14:00|15:00|16:00|17:20", text):
        return "evening"
    return "unknown"


def get_hour_range(text):
    # T4
    text = normalize_text(text)

    match = re.search(r"(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})", text)

    if match:
        return f"{match.group(1)}-{match.group(2)}"

    if "1st" in text or "first" in text:
        return "09:30-10:50"

    if "2nd" in text or "second" in text:
        return "11:00-12:20"

    if "after 12:30" in text:
        return "12:30-end"

    if "after 12:00" in text or "after 12" in text:
        return "12:00-end"

    if "after 15:00" in text:
        return "15:00-end"

    if "after 16:00" in text:
        return "16:00-end"

    return ""


def get_note(text):
    # T5
    text = normalize_text(text)

    notes = []

    if "prefers second period" in text:
        notes.append("prefers second period")

    if "museum" in text:
        notes.append("museum")

    if "classroom" in text:
        notes.append("classroom")

    if "two classes in a row" in text:
        notes.append("two classes in a row")

    return "; ".join(notes)


def tokenize_availability():
    df = pd.read_csv(INPUT_FILE)

    # Standardize column names from current CSV
    df = df.rename(
        columns={
            "Course Code": "course_code",
            "Course Name ": "course_name",
            "Instructor ": "teacher_name",
            "Availability 1": "availability_1",
            "Availability 2": "availability_2",
        }
    )

    rows = []

    for _, row in df.iterrows():
        for availability_col in ["availability_1", "availability_2"]:
            raw_text = row.get(availability_col)

            if pd.isna(raw_text) or str(raw_text).strip() == "":
                continue

            rows.append(
                {
                    "course_code": row.get("course_code", ""),
                    "course_name": clean_course_name(
                        row.get("course_name", "")
                    ),
                    "teacher_name": row.get("teacher_name", ""),
                    "raw_availability": raw_text,
                    "availability_group": get_day_group(raw_text),
                    "days": get_days(raw_text),
                    "period_type": get_period_type(raw_text),
                    "hour_range": get_hour_range(raw_text),
                    "notes": get_note(raw_text),
                }
            )

    tokenized = pd.DataFrame(rows)
    tokenized.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved tokenized availability to {OUTPUT_FILE}")
    print(tokenized.head(20))

    return tokenized


if __name__ == "__main__":
    tokenize_availability()
