"""Ekstraksi gejala dari keluhan teks bebas, grounded ke knowledge base.

Tujuan: mengubah kalimat owner ("kucing saya mengejan saat pipis dan tidak mau
makan") menjadi daftar gejala terstruktur yang dikenali sistem (name_id), agar
bisa diumpankan ke model ML symptom->disease dan grounding.

Pendekatan (tanpa dependensi berat):
1. Bangun indeks gejala dari KB (name_id, name, body_system, red_flag).
2. Tambah sinonim/kata kunci Bahasa Indonesia umum -> name_id.
3. Cocokkan via (a) keyword containment, (b) kemiripan token (difflib).
LLM-assisted extraction tersedia terpisah di suggestion engine bila ada kunci API.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..data_loader import KnowledgeBase
from .schemas import ExtractedSymptom

# Kamus kata kunci -> gejala (kanonik via substring keluhan). Nilai dipakai
# untuk mempertegas pencocokan istilah awam Bahasa Indonesia.
KEYWORD_HINTS: dict[str, list[str]] = {
    "muntah": ["muntah"],
    "mual": ["muntah"],
    "diare": ["diare", "mencret", "berak cair", "bab cair"],
    "mencret": ["diare", "mencret"],
    "berdarah": ["berdarah", "darah"],
    "lemas": ["lemas", "lesu", "lemah", "tidak bertenaga"],
    "lesu": ["lemas", "lesu"],
    "tidak mau makan": ["nafsu makan", "tidak makan", "anoreksia"],
    "nafsu makan": ["nafsu makan", "tidak makan"],
    "demam": ["demam", "panas"],
    "batuk": ["batuk"],
    "bersin": ["bersin"],
    "sesak": ["sesak", "sulit bernapas", "napas berat"],
    "gatal": ["gatal", "garuk"],
    "kejang": ["kejang"],
    "pincang": ["pincang", "lumpuh"],
    "pipis": ["pipis", "kencing", "urinasi", "buang air kecil"],
    "mengejan": ["mengejan", "ngeden"],
    "minum": ["minum", "haus"],
    "kurus": ["berat badan turun", "kurus", "berat turun"],
    "bengkak": ["bengkak", "benjolan"],
    "kuning": ["kuning", "jaundice", "ikterus"],
}


# Kata umum / nama spesies / stopword yang TIDAK boleh memicu fuzzy match
# (mencegah false-positive seperti "kucing" cocok ke "anak kucing").
STOPWORDS: set[str] = {
    "kucing", "anjing", "kelinci", "hamster", "ayam", "ikan", "burung", "reptil",
    "hewan", "peliharaan", "saya", "punya", "milik", "yang", "dan", "atau", "tapi",
    "tidak", "mau", "ada", "ini", "itu", "dia", "nya", "juga", "sudah", "belum",
    "saat", "sangat", "agak", "sedikit", "banyak", "kadang", "sering", "lagi",
    "dengan", "untuk", "pada", "dari", "ke", "di", "se", "anak", "dok", "dokter",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


@dataclass
class _SymptomEntry:
    name_id: str
    name: str | None
    body_system: str | None
    is_red_flag: bool
    norm_terms: list[str]


class SymptomExtractor:
    """Pencocok gejala berbasis knowledge base (cepat & offline)."""

    def __init__(self, kb: KnowledgeBase, category_slug: str | None = None):
        self.kb = kb
        self.category_slug = category_slug
        self._entries = self._build_index(kb, category_slug)

    def _build_index(
        self, kb: KnowledgeBase, category_slug: str | None
    ) -> list[_SymptomEntry]:
        diseases = (
            kb.diseases_for_category(category_slug) if category_slug else kb.diseases
        )
        seen: dict[str, _SymptomEntry] = {}
        for d in diseases:
            for s in d.get("symptoms", []):
                name_id = s.get("name_id") or s.get("name")
                if not name_id or name_id in seen:
                    continue
                terms = {_normalize(name_id)}
                if s.get("name"):
                    terms.add(_normalize(s["name"]))
                seen[name_id] = _SymptomEntry(
                    name_id=name_id,
                    name=s.get("name"),
                    body_system=s.get("body_system"),
                    is_red_flag=bool(s.get("is_red_flag", False)),
                    norm_terms=[t for t in terms if t],
                )
        return list(seen.values())

    def extract(self, text: str, threshold: float = 0.62) -> list[ExtractedSymptom]:
        """Kembalikan gejala terdeteksi, terurut dari skor tertinggi."""
        norm = _normalize(text)
        if not norm:
            return []
        tokens = set(norm.split())
        results: dict[str, ExtractedSymptom] = {}

        for entry in self._entries:
            best_score = 0.0
            matched_text = None

            # (a) containment langsung istilah gejala dalam keluhan
            for term in entry.norm_terms:
                if term and term in norm:
                    best_score = max(best_score, 0.95)
                    matched_text = term

            # (b) overlap kata kunci awam (KEYWORD_HINTS)
            if best_score < 0.95:
                for kw, hints in KEYWORD_HINTS.items():
                    if kw in norm:
                        for hint in hints:
                            if any(hint in t for t in entry.norm_terms):
                                best_score = max(best_score, 0.8)
                                matched_text = kw

            # (c) kemiripan token bertahap (fuzzy) untuk salah ketik / variasi.
            #     Gating ketat: abaikan stopword & token pendek, ratio tinggi.
            if best_score < threshold:
                fuzzy_best = 0.0
                for term in entry.norm_terms:
                    for term_tok in term.split():
                        if len(term_tok) < 5 or term_tok in STOPWORDS:
                            continue
                        for tok in tokens:
                            if len(tok) < 5 or tok in STOPWORDS:
                                continue
                            ratio = SequenceMatcher(None, term_tok, tok).ratio()
                            if ratio >= 0.86 and ratio > fuzzy_best:
                                fuzzy_best = ratio
                                matched_text = tok
                if fuzzy_best > best_score:
                    best_score = fuzzy_best

            if best_score >= threshold:
                results[entry.name_id] = ExtractedSymptom(
                    name_id=entry.name_id,
                    name=entry.name,
                    body_system=entry.body_system,
                    is_red_flag=entry.is_red_flag,
                    score=round(min(best_score, 1.0), 3),
                    matched_text=matched_text,
                )

        return sorted(results.values(), key=lambda s: s.score, reverse=True)

    def merge_known(self, symptoms_name_id: list[str]) -> list[ExtractedSymptom]:
        """Bungkus gejala yang sudah pasti (mis. dipilih dokter) menjadi terstruktur."""
        index = {e.name_id: e for e in self._entries}
        out: list[ExtractedSymptom] = []
        for nid in symptoms_name_id:
            e = index.get(nid)
            if e:
                out.append(ExtractedSymptom(
                    name_id=e.name_id, name=e.name, body_system=e.body_system,
                    is_red_flag=e.is_red_flag, score=1.0, matched_text=nid,
                ))
            else:
                out.append(ExtractedSymptom(name_id=nid, score=1.0, matched_text=nid))
        return out


if __name__ == "__main__":
    from ..data_loader import load_knowledge_base

    kb = load_knowledge_base()
    ex = SymptomExtractor(kb, category_slug="cat")
    sample = "kucing saya mengejan saat pipis, ada darah dan tidak mau makan, lemas"
    for s in ex.extract(sample):
        print(f"  {s.score:>5}  {s.name_id}  (red_flag={s.is_red_flag})")
