"""Smart Data Platform — orkestrasi data, ML, dan learning loop terintegrasi.

Modul ini menjadi titik masuk tunggal untuk:
- AI agent (manifest + doctor + pipeline JSON)
- DevOps / CI (jalankan langkah pipeline terstruktur)
- Admin dashboard (status registry & lineage)

Pakai:
    python -m sobatpaws.platform.doctor
    python -m sobatpaws.platform.pipeline --list
    python -m sobatpaws.platform.pipeline --step train_ml
    python -m sobatpaws.platform.registry --refresh
"""

from .manifest import PLATFORM_MANIFEST, get_pipeline_steps
from .doctor import run_doctor
from .registry import load_registry, refresh_registry

__all__ = [
    "PLATFORM_MANIFEST",
    "get_pipeline_steps",
    "run_doctor",
    "load_registry",
    "refresh_registry",
]
