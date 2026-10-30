"""Standalone ML02 CLI and registration hooks for the parent integration."""

import argparse
import json
import sys
from pathlib import Path

from .service import MarketError, MarketService


def company_arguments(parser):
    parser.add_argument(
        "--input",
        type=Path,
        help="Prepared JSON list or object with rows; default: approved sources",
    )
    parser.add_argument("--output", type=Path, help="Write row-evidence CSV")
    return parser


def run_company_report(service, args):
    if args.input:
        try:
            prepared = json.loads(args.input.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            raise MarketError(f"Không đọc được prepared JSON: {error}") from error
        rows = prepared.get("rows") if isinstance(prepared, dict) else prepared
    else:
        rows = service.prepare()["rows"]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise MarketError("Prepared JSON cần danh sách rows dạng object.")
    result = service.company_report(rows)
    if args.output:
        try:
            args.output.write_text(result["csv"], encoding="utf-8")
        except OSError as error:
            raise MarketError(f"Không xuất được CSV công ty: {error}") from error
    return result


def main():
    parser = company_arguments(argparse.ArgumentParser(description="ML02 company identity audit"))
    args = parser.parse_args()
    try:
        result = run_company_report(MarketService(), args)
    except MarketError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
