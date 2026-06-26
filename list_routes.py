#!/usr/bin/env python3
"""List all FastAPI routes."""
from sobatpaws.api.main import app
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f'{sorted(route.methods)} {route.path}')
