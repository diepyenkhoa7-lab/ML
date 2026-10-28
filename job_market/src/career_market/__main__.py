"""Local raw preview CLI, sharing the dashboard's business interface."""

import argparse
import json
import sys
from dataclasses import asdict

from . import MarketError, MarketService


def main() -> int:
    parser = argparse.ArgumentParser(description="Xem nguồn tin tuyển dụng gốc đã duyệt.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sources", help="Danh mục nguồn và xuất xứ")
    preview = commands.add_parser("preview", help="Kiểm tra và xem raw dạng JSON")
    preview.add_argument("source_id")
    preview.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    try:
        service = MarketService()
        if args.command == "sources":
            result = [asdict(source) for source in service.sources()]
        else:
            result = asdict(service.preview(args.source_id, args.limit))
    except MarketError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
