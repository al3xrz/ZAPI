"""
Manual smoke-check runner for the ZAPI library.

Usage:
    ZABBIX_URL="https://zabbix.example.com" \
    ZABBIX_USER="Admin" \
    ZABBIX_PASSWORD="secret" \
    python manual_check.py \
        --group "Linux servers" \
        --item-transforms examples/item_transforms.example.json

The group check is optional; without --group the script checks API version and
login/logout only.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PARENT_DIR = PACKAGE_DIR.parent

if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in ("", None) else default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run manual smoke checks against a Zabbix server."
    )
    parser.add_argument("--url", default=_env("ZABBIX_URL"), help="Zabbix base URL")
    parser.add_argument("--user", default=_env("ZABBIX_USER"), help="Zabbix username")
    parser.add_argument(
        "--password",
        default=_env("ZABBIX_PASSWORD"),
        help="Zabbix password",
    )
    parser.add_argument(
        "--api-version",
        type=int,
        default=int(_env("ZABBIX_API_VERSION", "7")),
        help="Major Zabbix API version. Use 5 for old user.login payload.",
    )
    parser.add_argument(
        "--group",
        default=_env("ZABBIX_GROUP"),
        help="Optional host group name for get_group_id/get_group_info checks.",
    )
    parser.add_argument(
        "--item-transforms",
        default=_env("ZABBIX_ITEM_TRANSFORMS"),
        help=(
            "Optional path to JSON item transformation rules. "
            "Used only with --group."
        ),
    )
    return parser.parse_args()


def require_config(args: argparse.Namespace) -> None:
    missing = [
        name
        for name, value in (
            ("ZABBIX_URL or --url", args.url),
            ("ZABBIX_USER or --user", args.user),
            ("ZABBIX_PASSWORD or --password", args.password),
        )
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required config: {joined}")


def load_item_transforms(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as file:
        transforms = json.load(file)

    if not isinstance(transforms, dict):
        raise ValueError("Item transforms config must be a JSON object")

    for key, rule in transforms.items():
        if not isinstance(key, str) or not isinstance(rule, dict):
            raise ValueError("Each item transform must be an object keyed by item key")

    return transforms


async def main() -> None:
    args = parse_args()
    require_config(args)

    try:
        from ZAPI import Zabbix
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Missing Python dependency: {exc.name}. "
            "Install project dependencies before running checks."
        ) from exc

    item_transforms = None
    if args.item_transforms:
        item_transforms = load_item_transforms(args.item_transforms)
        print(f"Loaded item transforms: {len(item_transforms)} rules")

    print("1. Checking API version...")
    version_response = await Zabbix.get_api_version(args.url)
    print(f"   apiinfo.version response: {version_response}")

    zabbix = Zabbix(
        url=args.url,
        username=args.user,
        password=args.password,
        api_version=args.api_version,
        item_transforms=item_transforms,
    )

    print("2. Logging in...")
    await zabbix.login()
    print("   login ok")

    if args.group:
        print(f'3. Checking group "{args.group}"...')
        group_id = await zabbix.get_group_id(args.group)
        print(f"   group id: {group_id}")

        print("4. Loading group info...")
        group_info = await zabbix.get_group_info(args.group)
        print(f"   hosts loaded: {len(group_info)}")
    else:
        print("3. Group checks skipped; pass --group to enable them.")

    print("5. Logging out...")
    await zabbix.logout()
    print("   logout ok")


if __name__ == "__main__":
    asyncio.run(main())
