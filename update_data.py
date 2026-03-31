from __future__ import annotations

import argparse
import logging

from nyfs.ingestion import refresh_dashboard_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh NYFS local dashboard data.")
    parser.add_argument(
        "--api-mode",
        choices=["auto", "v3", "legacy"],
        default="auto",
        help="Use auto mode (v3 then legacy), explicit v3, or explicit legacy SODA $limit/$offset mode.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail instead of falling back to the local CSV when the API is unavailable.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = parse_args()
    metadata = refresh_dashboard_data(
        api_mode=args.api_mode,
        allow_fallback=not args.no_fallback,
    )
    logging.info("Refresh complete: %s", metadata)


if __name__ == "__main__":
    main()
