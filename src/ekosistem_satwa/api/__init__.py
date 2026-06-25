"""Layanan API Ekosistem Satwa (FastAPI) untuk integrasi aplikasi dokter.

Mengekspor `app` agar entrypoint `ekosistem_satwa.api:app` & `ekosistem_satwa.api.main:app`
sama-sama berfungsi.
"""
from .main import app

__all__ = ["app"]
