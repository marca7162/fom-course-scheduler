"""Import an enrollment workbook, rebuild derived data, and generate schedules."""

import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from scripts.excel_to_csv import convert_excel
from scripts.tokenized_enrollment import tokenize_enrollment
from scripts.tokenize_avalability import tokenize_availability
from scripts.orchestrator import run_scheduler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    convert_excel(Path(args.input_file))
    tokenize_enrollment()
    tokenize_availability()

    result = run_scheduler(
        rooms_path=str(project_root / "csv_files" / "rooms.csv"),
        enroll_path=str(project_root / "csv_files" / "tokenized_enrollment.csv"),
        avail_path=str(project_root / "csv_files" / "tokenized_availability.csv"),
        output_dir=str(project_root / "output"),
    )
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
