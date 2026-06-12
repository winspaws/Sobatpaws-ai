"""Layanan API Sobatpaws (FastAPI) untuk integrasi aplikasi dokter.

Mengekspor `app` agar entrypoint `sobatpaws.api:app` & `sobatpaws.api.main:app`
sama-sama berfungsi.
"""
from .main import app

__all__ = ["app"]
