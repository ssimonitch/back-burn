#!/bin/bash
# Development server startup script

export APP_ENVIRONMENT=local
uv run poe dev
