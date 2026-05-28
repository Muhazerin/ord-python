"""Adapters that translate framework metadata into ORD model objects.

Adapters live in submodules so optional framework dependencies (FastAPI,
FastMCP) can stay opt-in. Import the adapter you need directly, e.g.
``from ord.adapters.fastapi import apiresource_from_fastapi``.
"""
