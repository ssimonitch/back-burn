#!/usr/bin/env python3
"""
Publish/copy the OpenAPI schema for frontend consumption.

By default, copies backend/openapi.json to ../frontend/openapi.json.

Usage:
    python scripts/publish_openapi.py [--dest PATH] [--generate]

    or via poe:
    uv run poe publish-openapi
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).parent.parent
    backend_schema = project_root / "openapi.json"

    parser = argparse.ArgumentParser(description="Publish OpenAPI schema to frontend.")
    parser.add_argument(
        "--dest",
        type=str,
        default=str(project_root.parent / "frontend" / "openapi.json"),
        help="Destination path for openapi.json (defaults to ../frontend/openapi.json)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate schema if not present before publishing.",
    )
    args = parser.parse_args()

    dest_path = Path(args.dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if not backend_schema.exists():
        if not args.generate:
            print(
                "❌ openapi.json not found. Run 'uv run poe generate-openapi' or pass --generate."
            )
            return 1
        # Generate on demand
        try:
            # Avoid circular import issues by invoking the script as a module
            import subprocess

            result = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "generate_openapi.py")],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                print(result.stdout)
                print(result.stderr)
                print("❌ Failed to generate openapi.json")
                return result.returncode
        except Exception as exc:
            print(f"❌ Error generating openapi.json: {exc}")
            return 1

    try:
        shutil.copyfile(backend_schema, dest_path)
        print(f"✅ Published OpenAPI schema to: {dest_path}")
        return 0
    except Exception as exc:
        print(f"❌ Failed to publish OpenAPI schema: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
