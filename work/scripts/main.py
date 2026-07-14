import argparse
import json
import sys
from pathlib import Path
import glob

sys.path.append(str(Path(__file__).parent.parent))

from scripts.orchestrator import run_scheduler

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent

    avail_pattern = str(project_root / "csv_files" / "tokenized_availability*.csv")
    avail_files = glob.glob(avail_pattern)
    if not avail_files:
        raise FileNotFoundError("No availability CSV found in csv_files/")
    avail_path = avail_files[0]

    result = run_scheduler(
        rooms_path=str(project_root / "csv_files" / "rooms.csv"),
        enroll_path=str(
            project_root / "csv_files" / "tokenized_enrollment.csv"
        ),
        avail_path=avail_path,
        output_dir=str(project_root / "work" / "output"),
    )

    if args.json:
        sys.stdout.write(json.dumps(result))
        sys.stdout.flush()
    else:
        print("✅ Scheduling complete!")
        print(f"Course‑Room rows: {len(result['course_room'])}")
        print(f"Teacher rows:     {len(result['teacher'])}")
        print(f"Student rows:     {len(result['student'])}")