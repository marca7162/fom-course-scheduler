import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "clean_enrollment.csv"
OUTPUT_FILE = ROOT / "tokenized_enrollment.csv"


def get_student_id(student_name):
    match = re.search(r"(\d+)", str(student_name))
    return int(match.group(1)) if match else None


def get_course_id(course_text):
    match = re.search(r"(\d+)", str(course_text))
    return int(match.group(1)) if match else None


def tokenize_enrollment():
    df = pd.read_csv(INPUT_FILE)

    rows = []

    course_columns = [
        "Course 1",
        "Course 2",
        "Course 3",
        "Course 4",
        "Course 5",
    ]

    for _, row in df.iterrows():
        student_id = get_student_id(row["Last name, first name"])

        for course_col in course_columns:
            course = row.get(course_col)

            if pd.isna(course) or str(course).strip() == "":
                continue

            course_id = get_course_id(course)

            rows.append({"student_id": student_id, "course_id": course_id})

    tokenized = pd.DataFrame(rows)

    tokenized.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved tokenized enrollment to {OUTPUT_FILE}")
    print(tokenized.head(20))

    return tokenized


if __name__ == "__main__":
    tokenize_enrollment()
