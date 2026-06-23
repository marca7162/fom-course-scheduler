import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "clean_availability.csv"
OUTPUT_FILE = ROOT / "tokenized_availability.csv"


def normalize_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip().lower()


def get_course_id(course_code):
    match = re.search(r"(\d+)", str(course_code))
    return int(match.group(1)) if match else None


def get_day_group(text):
    text = normalize_text(text)

    if "m/w" in text or "mw" in text:
        return "MW"
    if "t/th" in text or "tth" in text:
        return "TTH"
    if "tuesday" in text or "tuesdays" in text:
        return "T"
    if "thursday" in text or "thursdays" in text:
        return "TH"
    if "any time" in text or "anytime" in text:
        return "ALL"

    return "UNKNOWN"


def get_period_options(text):
    text = normalize_text(text)

    if "first or second" in text or "1st or second" in text:
        return "1,2"

    if "prefers second" in text:
        return "1,2"

    if "9:30-10:50" in text:
        return "1"

    if "11:00-12:20" in text:
        return "2"

    if "9:30-12:20" in text:
        return "1,2"

    if "10:30-13:50" in text:
        return "1,2"

    if "14:00-15:20" in text:
        return "5"

    if "16:00-17:20" in text:
        return "7"

    if "after 12:00" in text or "after 12" in text:
        return "3,4,5,6,7,8,9"

    if "after 12:30" in text:
        return "4,5,6,7,8,9"

    if "after 15:00" in text:
        return "6,7,8,9"

    if "after 16:00" in text:
        return "7,8,9"

    if "any time" in text or "anytime" in text:
        return "1,2,3,4,5,6,7,8,9"

    return ""


def get_preference(text):
    text = normalize_text(text)

    if "prefers second" in text:
        return "prefer_2"

    if "two classes in a row" in text:
        return "two_in_row"

    if "museum" in text:
        return "museum"

    if "classroom" in text:
        return "classroom"

    return "required"


def tokenize_availability():
    df = pd.read_csv(INPUT_FILE)

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
        avail1 = row.get("availability_1")
        avail2 = row.get("availability_2")

        no_avail1 = pd.isna(avail1) or str(avail1).strip() == ""
        no_avail2 = pd.isna(avail2) or str(avail2).strip() == ""

        # If no availability is listed, assume the course can be placed anywhere.
        if no_avail1 and no_avail2:
            rows.append(
                {
                    "course_id": get_course_id(row["course_code"]),
                    "teacher_name": row["teacher_name"],
                    "day_group": "ALL",
                    "period_options": "1,2,3,4,5,6,7,8,9",
                    "preference": "none",
                }
            )
            continue

        for col in ["availability_1", "availability_2"]:
            raw_text = row.get(col)

            if pd.isna(raw_text) or str(raw_text).strip() == "":
                continue

            rows.append(
                {
                    "course_id": get_course_id(row["course_code"]),
                    "teacher_name": row["teacher_name"],
                    "day_group": get_day_group(raw_text),
                    "period_options": get_period_options(raw_text),
                    "preference": get_preference(raw_text),
                }
            )

    tokenized = pd.DataFrame(rows)
    tokenized.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved cleaned tokenized availability to {OUTPUT_FILE}")
    print(tokenized)

    return tokenized

if __name__ == "__main__":
    tokenize_availability()
