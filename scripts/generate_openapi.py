#!/usr/bin/env python3
"""
OpenAPI Schema Generation Script

This script generates the OpenAPI schema from the FastAPI application and outputs
it as JSON. This ensures the frontend and backend maintain a consistent API contract.

Usage:
    python scripts/generate_openapi.py

    or via poe:
    uv run poe generate-openapi

The generated schema will be saved to:
    - openapi.json (in the project root)
"""

import json
import sys
from pathlib import Path

# Add the project root to the path so we can import the FastAPI app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from main import app
except ImportError as e:
    print(f"Error: Could not import FastAPI app: {e}")
    print("Make sure you're running this script from the backend directory")
    sys.exit(1)


def generate_openapi_schema():
    """Generate OpenAPI schema and save to JSON file."""
    try:
        # Get the OpenAPI schema from FastAPI
        openapi_schema = app.openapi()

        # Define output path (project root)
        output_path = project_root / "openapi.json"

        # Write schema to file with pretty formatting and stable key ordering
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False, sort_keys=True)

        # Print success message with schema info
        endpoint_count = len(openapi_schema.get("paths", {}))
        component_count = len(openapi_schema.get("components", {}).get("schemas", {}))

        print("✅ OpenAPI schema generated successfully!")
        print(f"📄 Output: {output_path}")
        print(f"🔗 Endpoints: {endpoint_count}")
        print(f"📋 Schemas: {component_count}")
        print(
            f"📦 API Version: {openapi_schema.get('info', {}).get('version', 'unknown')}"
        )

        return True

    except Exception as e:
        print(f"❌ Error generating OpenAPI schema: {e}")
        return False


if __name__ == "__main__":
    success = generate_openapi_schema()
    sys.exit(0 if success else 1)
