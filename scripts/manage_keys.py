#!/usr/bin/env python3
"""CLI tool to create, list, and revoke API keys.

Usage:
    python scripts/manage_keys.py create --name 'Marco'
    python scripts/manage_keys.py list
    python scripts/manage_keys.py revoke --id <key_id>
"""

from __future__ import annotations

import argparse
import sys


def cmd_create(args: argparse.Namespace) -> None:
    from mcp_presentation_video.api.auth import generate_api_key

    plaintext, record = generate_api_key(args.name)
    print(f"API Key created for '{args.name}'")
    print(f"  Key ID:  {record['key_id']}")
    print(f"  API Key: {plaintext}")
    print()
    print("Save this key — it will not be shown again.")


def cmd_list(args: argparse.Namespace) -> None:
    from mcp_presentation_video.api.auth import list_api_keys

    keys = list_api_keys()
    if not keys:
        print("No API keys found.")
        return
    print(f"{'Key ID':<18} {'Name':<20} {'Created'}")
    print("-" * 60)
    for k in keys:
        print(f"{k['key_id']:<18} {k['name']:<20} {k['created_at']}")


def cmd_revoke(args: argparse.Namespace) -> None:
    from mcp_presentation_video.api.auth import revoke_api_key

    if revoke_api_key(args.id):
        print(f"Key {args.id} revoked.")
    else:
        print(f"Key {args.id} not found.")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage API keys for the presentation video server")
    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Create a new API key")
    create_p.add_argument("--name", required=True, help="Name for the key holder")
    create_p.set_defaults(func=cmd_create)

    list_p = sub.add_parser("list", help="List all API keys")
    list_p.set_defaults(func=cmd_list)

    revoke_p = sub.add_parser("revoke", help="Revoke an API key")
    revoke_p.add_argument("--id", required=True, help="Key ID to revoke")
    revoke_p.set_defaults(func=cmd_revoke)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
