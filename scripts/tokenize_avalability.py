from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent

INPUT_FILE = ROOT / "clean_availability.csv"
COUNTS_FILE = ROOT / "clean_counts.csv"
OUTPUT_FILE = ROOT / "tokenized_availability.csv"


ONCE_PER_WEEK_COURSES = {
    "MADR 3012",  # Internship In Spain
    "MADR 4901",  # Research Laboratory In Psychology
}


def normalize_text(text):
    if pd.isna(text):
        return ""
    return str(text).strip().lower()


def get_course_id(course_text):
    parts = str(course_text).strip().split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    return str(course_text).strip()


def is_once_per_week_course(course_id):
    return course_id in ONCE_PER_WEEK_COURSES


def load_credit_lookup():
    counts = pd.read_csv(COUNTS_FILE)

    counts = counts.rename(
        columns={
            "Full Course List": "full_course_list",
            "Credits": "credits",
        }
    )

    counts["full_course_list"] = (
        counts["full_course_list"].astype(str).str.strip()
    )
    counts = counts[counts["full_course_list"] != ""]
    counts = counts[
        ~counts["full_course_list"].str.startswith("Notes", na=False)
    ]

    counts["course_id"] = counts["full_course_list"].apply(get_course_id)
    counts["credits"] = pd.to_numeric(counts["credits"], errors="coerce")

    return dict(zip(counts["course_id"], counts["credits"]))


def add_period_8_if_five_credits(period_options, course_id, credit_lookup):
    credits = credit_lookup.get(course_id)

    if credits == 5:
        options = period_options.split(",") if period_options else []

        if "8" not in options:
            options.append("8")

        return ",".join(options)

    return period_options


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


def get_base_period_options(text):
    text = normalize_text(text)

    if "any time" in text or "anytime" in text:
        return "1,2,3,4,5,6,7"

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

    if "after 12:30" in text:
        return "4,5,6,7"

    if "after 12:00" in text or "after 12" in text:
        return "3,4,5,6,7"

    if "after 15:00" in text:
        return "6,7"

    if "after 16:00" in text:
        return "7"

    return ""


def get_period_options(text, course_id, credit_lookup):
    base_options = get_base_period_options(text)
    return add_period_8_if_five_credits(base_options, course_id, credit_lookup)


def get_preference(text, course_id):
    text = normalize_text(text)

    if is_once_per_week_course(course_id):
        return "once_per_week"

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
    credit_lookup = load_credit_lookup()

    df = pd.read_csv(INPUT_FILE)

    df = df.rename(
        columns={
            # old headers
            "Course Code": "course_id",
            "Course Name": "course_name",
            "Course Name ": "course_name",
            "Instructor": "teacher_name",
            "Instructor ": "teacher_name",
            "Availability 1": "availability_1",
            "Availability 2": "availability_2",
            # new snake_case headers
            "course_code": "course_id",
            "course_name": "course_name",
            "instructor": "teacher_name",
            "availability_1": "availability_1",
            "availability_2": "availability_2",
        }
    )

    required_columns = {
        "course_id",
        "course_name",
        "teacher_name",
        "availability_1",
        "availability_2",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns in clean_availability.csv: {missing_columns}"
        )

    rows = []

    for _, row in df.iterrows():
        course_id = get_course_id(row["course_id"])
        teacher_name = row["teacher_name"]

        avail1 = row.get("availability_1")
        avail2 = row.get("availability_2")

        no_avail1 = pd.isna(avail1) or str(avail1).strip() == ""
        no_avail2 = pd.isna(avail2) or str(avail2).strip() == ""

        if no_avail1 and no_avail2:
            period_options = add_period_8_if_five_credits(
                "1,2,3,4,5,6,7", course_id, credit_lookup
            )

            rows.append(
                {
                    "course_id": course_id,
                    "teacher_name": teacher_name,
                    "day_group": "ALL",
                    "period_options": period_options,
                    "preference": (
                        "once_per_week"
                        if is_once_per_week_course(course_id)
                        else "none"
                    ),
                }
            )

            continue

        for col in ["availability_1", "availability_2"]:
            raw_text = row.get(col)

            if pd.isna(raw_text) or str(raw_text).strip() == "":
                continue

            rows.append(
                {
                    "course_id": course_id,
                    "teacher_name": teacher_name,
                    "day_group": (
                        "ALL"
                        if is_once_per_week_course(course_id)
                        else get_day_group(raw_text)
                    ),
                    "period_options": get_period_options(
                        raw_text,
                        course_id,
                        credit_lookup,
                    ),
                    "preference": get_preference(raw_text, course_id),
                }
            )

    tokenized = pd.DataFrame(rows)

    tokenized = tokenized.drop_duplicates()
    tokenized = tokenized.reset_index(drop=True)

    tokenized.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved tokenized availability to {OUTPUT_FILE}")
    print(tokenized)

    return tokenized


if __name__ == "__main__":
    tokenize_availability()
