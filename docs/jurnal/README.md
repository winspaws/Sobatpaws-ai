# Jurnal Perhewanan — Ekosistem Satwa

Dokumentasi ilmiah & edukatif tentang hewan peliharaan: spesies, ras, varian, kesehatan, dan penyakit.

**Maintainer:** Agent `research` (Risa) — Hermes profile Naincode AI Dept.

## Hubungan dengan Knowledge Base

| Jurnal (Markdown) | JSON (Runtime) |
|-------------------|----------------|
| Narasi, referensi, konteks klinis | Data terstruktur untuk API & ML |
| `docs/jurnal/` | `data/categories.json`, `data/breeds/`, `data/clinical/` |

Perubahan klinis yang mempengaruhi aplikasi **harus** juga di-update di JSON curated, lalu jalankan pipeline `agent_bootstrap`.

## Struktur

```
jurnal/
├── INDEX.md              # Daftar lengkap topik + status dokumentasi
├── RESEARCH-LOG.md         # Log aktivitas riset
├── spesies/                # 10 kategori spesies
├── ras/                    # Monograf per ras (slug)
├── varian/                 # Sub-ras, warna, morph
├── penyakit/               # Monograf penyakit (slug)
├── kesehatan/              # Topik umum (vaksinasi, nutrisi, dll.)
└── _template/              # Template penulisan
```

## Status dokumentasi

| Status | Arti |
|--------|------|
| `draft` | Draft awal, belum review |
| `reviewed` | Review internal, siap sinkron |
| `synced` | Selaras dengan JSON KB |

## Regenerate index

```bash
python scripts/build_journal_index.py
```

## Disclaimer

Konten edukatif untuk mendukung keputusan klinis. Diagnosa dan resep final wajib oleh dokter hewan berlisensi.
