"""Tiny FastAPI app used to demonstrate the ORD adapter end-to-end.

Run ``python emit_ord.py`` from this directory to see the validated ORD
document this app would publish.
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(
    title="Demo Greeter Service",
    version="1.0.0",
    description="Returns a friendly hello.",
)


@app.get("/hello")
def hello(name: str = "world") -> dict[str, str]:
    return {"message": f"hello, {name}"}
