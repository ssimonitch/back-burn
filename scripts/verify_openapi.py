#!/usr/bin/env python3
"""
OpenAPI Schema Verification Script

This script verifies that the current openapi.json file matches what would be
generated from the current FastAPI application. This is useful for CI/CD to
ensure the schema stays in sync with code changes.

Usage:
    python scripts/verify_openapi.py

    or via poe:
    uv run poe verify-openapi

Exit codes:
    0: Schema is up-to-date
    1: Schema is out-of-date or error occurred
"""

import argparse
import json
import sys
from collections.abc import Hashable, Mapping
from pathlib import Path
from typing import Any, cast

# Add the project root to the path so we can import the FastAPI app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from main import app
except ImportError as e:
    print(f"❌ Error: Could not import FastAPI app: {e}")
    print("Make sure you're running this script from the backend directory")
    sys.exit(1)


def verify_openapi_schema(
    auto_update: bool = False, validate_spec: bool = True
) -> bool:
    """Verify that the current schema matches the generated schema.

    Args:
        auto_update: If True, regenerate and write openapi.json when mismatch.
        validate_spec: If True, attempt to validate schemas with openapi-spec-validator if available.
    """
    try:
        # Get current schema from FastAPI
        current_schema = app.openapi()

        # Read existing schema file
        schema_path = project_root / "openapi.json"

        if not schema_path.exists():
            print("❌ Error: openapi.json does not exist")
            print("Run 'uv run poe generate-openapi' to create it")
            return False

        with open(schema_path, encoding="utf-8") as f:
            existing_schema = json.load(f)

        # Optionally validate schemas using openapi-spec-validator (if installed)
        if validate_spec:
            try:
                # Lazy import to keep this optional
                from openapi_spec_validator import validate
                from openapi_spec_validator.validation.exceptions import (
                    OpenAPIValidationError,
                )

                try:
                    validate(cast(Mapping[Hashable, Any], existing_schema))
                except OpenAPIValidationError as exc:
                    print(f"❌ Existing openapi.json is invalid: {exc}")
                    # If invalid and auto_update is enabled, fall back to regenerating
                    if auto_update:
                        print("🛠️  Regenerating openapi.json due to invalid schema...")
                        _write_schema(schema_path, current_schema)
                        print("✅ openapi.json regenerated.")
                        return True
                    else:
                        return False

                # Validate the current schema too
                try:
                    validate(cast(Mapping[Hashable, Any], current_schema))
                except OpenAPIValidationError as exc:
                    print(f"❌ Generated schema is invalid: {exc}")
                    return False
            except Exception:
                # Validator not installed or unexpected error; proceed without blocking
                pass

        # Compare schemas (normalize by converting to JSON strings)
        current_json = json.dumps(current_schema, sort_keys=True, indent=2)
        existing_json = json.dumps(existing_schema, sort_keys=True, indent=2)

        if current_json == existing_json:
            endpoint_count = len(current_schema.get("paths", {}))
            component_count = len(
                current_schema.get("components", {}).get("schemas", {})
            )

            print("✅ OpenAPI schema is up-to-date!")
            print(f"📄 Schema: {schema_path}")
            print(f"🔗 Endpoints: {endpoint_count}")
            print(f"📋 Schemas: {component_count}")
            print(
                f"📦 API Version: {current_schema.get('info', {}).get('version', 'unknown')}"
            )
            return True
        else:
            print("❌ OpenAPI schema is out-of-date!")
            print("The current FastAPI application would generate a different schema.")
            print("Run 'uv run poe generate-openapi' to update it.")

            # Try to identify what changed
            try:
                current_paths = set(current_schema.get("paths", {}).keys())
                existing_paths = set(existing_schema.get("paths", {}).keys())

                if current_paths != existing_paths:
                    new_paths = current_paths - existing_paths
                    removed_paths = existing_paths - current_paths

                    if new_paths:
                        print(f"📢 New endpoints: {', '.join(new_paths)}")
                    if removed_paths:
                        print(f"🗑️  Removed endpoints: {', '.join(removed_paths)}")

                current_schemas = set(
                    current_schema.get("components", {}).get("schemas", {}).keys()
                )
                existing_schemas = set(
                    existing_schema.get("components", {}).get("schemas", {}).keys()
                )

                if current_schemas != existing_schemas:
                    new_schemas = current_schemas - existing_schemas
                    removed_schemas = existing_schemas - current_schemas

                    if new_schemas:
                        print(f"📋 New schemas: {', '.join(new_schemas)}")
                    if removed_schemas:
                        print(f"🗑️  Removed schemas: {', '.join(removed_schemas)}")

                # Provide a small unified diff header for info/version changes
                current_info = current_schema.get("info", {})
                existing_info = existing_schema.get("info", {})
                if current_info != existing_info:
                    print("ℹ️  Info section changed:")
                    print(f"   existing: {existing_info}")
                    print(f"   current : {current_info}")

            except Exception as e:
                print(f"Could not analyze differences: {e}")

            if auto_update:
                print("🛠️  Auto-update enabled. Regenerating openapi.json...")
                _write_schema(schema_path, current_schema)
                print("✅ openapi.json updated.")
                return True
            else:
                return False

    except Exception as e:
        print(f"❌ Error verifying OpenAPI schema: {e}")
        return False


def _write_schema(schema_path: Path, schema: dict) -> None:
    """Write schema JSON with pretty formatting and stable key ordering."""
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify OpenAPI schema is up-to-date.")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Automatically regenerate openapi.json when mismatch is detected.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation via openapi-spec-validator.",
    )
    args = parser.parse_args()

    success = verify_openapi_schema(
        auto_update=args.update, validate_spec=not args.no_validate
    )
    sys.exit(0 if success else 1)
