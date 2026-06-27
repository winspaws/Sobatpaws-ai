"""
Veterinary Behavioral Medicine Module — Pengetahuan Perilaku & Psikiatri Hewan
Mencakup diagnosis, analisis, dan rekomendasi untuk 10+ behavior conditions.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional

class BehaviorCategory(str, Enum):
    SEPARATION_ANXIETY = "separation_anxiety"
    COMPULSIVE_DISORDER = "compulsive_disorder"
    COGNITIVE_DYSFUNCTION = "cognitive_dysfunction"
    FEAR_PHOBIA = "fear_phobia"
    AGGRESSION = "aggression"
    PICA = "pica"
    ELIMINATION_ISSUES = "elimination_issues"
    EXCESSIVE_VOCALIZATION = "excessive_vocalization"
    SLEEP_DISORDERS = "sleep_disorders"
    STEREOTYPIC_BEHAVIOR = "stereotypic_behavior"
    MATERNAL_BEHAVIOR = "maternal_behavior"
    PLAY_BEHAVIOR = "play_behavior"

BEHAVIOR_CONDITIONS = {
    "separation_anxiety": {
        "name_id": "Kecemasan Berpisah",
        "species": ["dog"],
        "description": "Kecemasan berlebihan saat ditinggal sendiri oleh pemilik.",
        "common_breeds": ["Labrador Retriever", "German Shepherd", "Border Collie", "Vizsla", "Cocker Spaniel"],
        "symptoms": [
            "Merusak barang (pintu, sofa, sepatu) saat ditinggal",
            "Menggonggong/melolong terus-menerus saat sendirian",
            "Buang air di rumah saat ditinggal",
            "Mengikuti pemilik kemana-mana (shadowing)",
            "Hipersalivasi (ngiler berlebihan)",
            "Muntah atau diare saat pemilik bersiap pergi",
            "Tidak mau makan saat sendirian",
            "Melukai diri (menjilat kaki sampai luka)",
        ],
        "causes": ["Perubahan rutinitas", "Trauma ditinggal", "Lingkungan baru", "Kurang stimulasi"],
        "red_flags": ["Self-injury (menjilat sampai luka)", "Menolak makan >24 jam", "Muntah terus-menerus"],
        "treatment": [
            {"type": "training", "priority": 1, "label": "Desensitisasi bertahap", "desc": "Latih hewan untuk tenang saat ditinggal, mulai dari 5 menit, naikkan bertahap."},
            {"type": "environment", "priority": 2, "label": "Pengayaan lingkungan", "desc": "Berikan puzzle toys, Kong isi camilan, atau mainan interaktif saat ditinggal."},
            {"type": "training", "priority": 3, "label": "Counter-conditioning", "desc": "Asosiasikan kepergian Anda dengan hal positif (treat khusus yang hanya diberikan saat Anda pergi)."},
            {"type": "pharma", "priority": 4, "label": "Konsultasi dokter hewan", "desc": "Untuk kasus berat, dokter mungkin meresepkan fluoxetine atau clomipramine."},
        ],
        "prevention": "Biasakan hewan sendirian sejak kecil. Jangan selalu menemani 24/7.",
        "vet_required": True,
    },
    "compulsive_disorder": {
        "name_id": "Gangguan Kompulsif",
        "species": ["dog", "cat"],
        "description": "Perilaku berulang tanpa tujuan yang jelas, dilakukan terus-menerus.",
        "common_breeds": ["Doberman", "German Shepherd", "Bull Terrier", "Siamese", "Burmese"],
        "symptoms": [
            "Mengejar ekor berputar-putar (spinning)",
            "Menjilat kaki/perut sampai botak atau luka (acral lick dermatitis)",
            "Menghisap kain/tempelan secara kompulsif (flank sucking)",
            "Berjalan mondar-mandir (pacing)",
            "Menggigit lalat imajiner (fly snapping)",
            "Vokalisasi berulang tanpa sebab",
            "Menggaruk berlebihan tanpa masalah kulit",
        ],
        "causes": ["Genetik (predisposisi ras)", "Stres kronis", "Kurang stimulasi mental", "Konflik lingkungan"],
        "red_flags": ["Luka akibat menjilat berlebihan", "Berat badan turun karena pacing terus-menerus"],
        "treatment": [
            {"type": "environment", "priority": 1, "label": "Perkaya lingkungan", "desc": "Tambah stimulasi mental: puzzle toys, nose work, latihan kepatuhan."},
            {"type": "training", "priority": 2, "label": "Interrupt & Redirect", "desc": "Ganggu perilaku kompulsif dengan suara/command, lalu alihkan ke aktivitas positif."},
            {"type": "behavioral", "priority": 3, "label": "Jadwal rutin", "desc": "Buat jadwal harian yang konsisten: makan, jalan, bermain, istirahat."},
            {"type": "pharma", "priority": 4, "label": "Konsultasi dokter hewan", "desc": "Kasus berat mungkin但uh fluoxetine atau clomipramine."},
        ],
        "prevention": "Stimulasi mental cukup. Jangan biarkan bosan berjam-jam.",
        "vet_required": True,
    },
    "cognitive_dysfunction": {
        "name_id": "Disfungsi Kognitif (Pikun)",
        "species": ["dog", "cat"],
        "description": "Penurunan fungsi kognitif pada hewan senior (7+ tahun), mirip Alzheimer pada manusia.",
        "common_breeds": ["Semua ras senior"],
        "symptoms": [
            "Bingung di rumah sendiri (tersesat di sudut)",
            "Lupa perintah yang sudah dikuasai",
            "Buang air di tempat yang tidak seharusnya (padahal sudah toilet trained)",
            "Siklus tidur terbalik (tidur siang, bangun malam)",
            "Menatap kosong ke dinding",
            "Perubahan interaksi sosial (lebih manja atau lebih menarik diri)",
            "Penurunan respons terhadap rangsangan",
            "Vokalisasi malam hari tanpa sebab jelas",
        ],
        "causes": ["Penuaan otak", "Akumulasi beta-amyloid", "Stres oksidatif", "Atrofi korteks serebral"],
        "red_flags": ["Tidak nafsu makan", "Vokalisasi malam hari terus-menerus", "Tidak merespon panggilan"],
        "treatment": [
            {"type": "environment", "priority": 1, "label": "Modifikasi lingkungan", "desc": "Pasang night light, jaga furniture tetap di tempat yang sama, gunakan alas anti-slip."},
            {"type": "dietary", "priority": 2, "label": "Diet pendukung otak", "desc": "Pertimbangkan makanan dengan omega-3, MCT oil, antioksidan (mis: Hill's b/d atau Purina NC)."},
            {"type": "training", "priority": 3, "label": "Stimulasi kognitif", "desc": "Mainan puzzle sederhana, latihan recall, sniffing games."},
            {"type": "pharma", "priority": 4, "label": "Konsultasi dokter", "desc": "Selegiline (Anipryl) bisa membantu. Terapi melatonin untuk sleep cycle."},
        ],
        "prevention": "Stimulasi mental sejak muda, diet kaya antioksidan.",
        "vet_required": True,
    },
    "fear_phobia": {
        "name_id": "Ketakutan & Fobia",
        "species": ["dog", "cat"],
        "description": "Reaksi ketakutan berlebihan terhadap stimulus tertentu.",
        "common_breeds": ["Border Collie", "Australian Shepherd", "Whippet", "Russian Blue"],
        "symptoms": [
            "Gemetar saat mendengar petir/kembang api",
            "Sembunyi di bawah tempat tidur/lemari",
            "Menggonggong/mengeong berlebihan",
            "Mencoba melarikan diri (lari keluar rumah, menerobos pagar)",
            "Hipersalivasi saat ada suara keras",
            "Buang air karena ketakutan",
            "Napas cepat/megap-megap (panting)",
            "Dilatasi pupil mata lebar",
        ],
        "causes": ["Genetik (sensitif)", "Pengalaman traumatis", "Sosialisasi kurang", "Sensitivitas pendengaran tinggi"],
        "triggers": ["Petir", "Kembang api", "Suara tembakan", "Suara motor/bom", "Dokter hewan", "Orang asing", "Anjing lain"],
        "red_flags": ["Melukai diri saat berusaha kabur", "Anoreksia karena ketakutan", "Diare karena stres akut"],
        "treatment": [
            {"type": "environment", "priority": 1, "label": "Safe space", "desc": "Sediakan tempat aman (crate dengan selimut, atau ruangan tanpa jendela) saat ada trigger."},
            {"type": "training", "priority": 2, "label": "Desensitisasi & Counter-conditioning", "desc": "Putar rekaman trigger dengan volume rendah, beri treat. Naikkan volume bertahap."},
            {"type": "product", "priority": 3, "label": "Alat bantu", "desc": "Thundershirt (vest penenang), Adaptil/DAP diffuser, musik klasik/white noise."},
            {"type": "supplement", "priority": 4, "label": "Suplemen penenang", "desc": "L-theanine (Anxitane), alpha-casozepine (Zylkene), atau melatonin (untuk anjing)."},
            {"type": "pharma", "priority": 5, "label": "Konsultasi dokter", "desc": "Untuk fobia berat, dokter mungkin resepkan alprazolam atau trazodone (short-term)."},
        ],
        "prevention": "Sosialisasi dini (3-16 minggu untuk anak anjing/kucing). Exposure positif ke berbagai suara.",
        "vet_required": True,
    },
    "aggression": {
        "name_id": "Agresi",
        "species": ["dog", "cat", "rabbit"],
        "description": "Perilaku agresif yang membahayakan hewan lain atau manusia.",
        "common_breeds": ["Terrier", "Chihuahua", "Jack Russell", "Persian", "Angora"],
        "symptoms": [
            "Menggeram/mendesis saat didekati",
            "Menggigit saat disentuh di area tertentu",
            "Agresi saat makan (food guarding)",
            "Agresi terhadap hewan lain di rumah",
            "Agresi territorial (galak sama orang datang)",
            "Agresi karena takut (fear-based aggression)",
            "Agresi possessive (mempertahankan mainan/tempat tidur)",
            "Agresi karena nyeri (pain-induced aggression)",
        ],
        "types": [
            {"type": "fear-based", "desc": "Agresi karena takut — ditandai dengan ekor di antara kaki, telinga ke belakang"},
            {"type": "possessive", "desc": "Agresi mempertahankan sumber daya — makanan, mainan, tempat tidur"},
            {"type": "territorial", "desc": "Agresi terhadap orang/hewan yang memasuki wilayah"},
            {"type": "redirected", "desc": "Agresi dialihkan ke orang/hewan terdekat saat frustrasi"},
            {"type": "pain-induced", "desc": "Agresi karena sakit — penting periksa ke dokter!"},
            {"type": "play", "desc": "Agresi saat bermain — biasanya tidak serius tapi perlu dikoreksi"},
        ],
        "red_flags": ["Menggigit sampai luka", "Agresi tanpa provokasi", "Agresi ke anak kecil", "Agresi ke pemilik"],
        "treatment": [
            {"type": "immediate", "priority": 0, "label": "KESELAMATAN DULU", "desc": "Jangan hukum fisik. Jangan tatap langsung. Jangan mendekat tiba-tiba. Pisahkan dari target agresi."},
            {"type": "training", "priority": 1, "label": "Konsultasi behavioris", "desc": "Agresi butuh penanganan profesional. Cari certified animal behaviorist."},
            {"type": "management", "priority": 2, "label": "Manajemen lingkungan", "desc": "Kelola pemicu: jangan biarkan hewan menjaga mangkuk makan, gunakan gate/pintu untuk pisah."},
            {"type": "training", "priority": 3, "label": "Counter-conditioning", "desc": "Asosiasikan trigger dengan hal positif. BUTUH BANTUAN PROFESIONAL."},
        ],
        "prevention": "Sosialisasi dini, training positif, tidak menggunakan hukuman fisik.",
        "vet_required": True,
        "dangerous": True,
    },
    "pica": {
        "name_id": "Pica (Makan Benda Non-Makanan)",
        "species": ["dog", "cat", "rabbit"],
        "description": "Kebiasaan memakan benda yang bukan makanan (batu, plastik, kain, dll).",
        "symptoms": [
            "Makan batu, tanah, pasir",
            "Mengunyah dan menelan plastik/kain",
            "Makan kotoran sendiri (coprophagia)",
            "Menggigiti dinding/tembok",
            "Makan tanaman hias (berbahaya jika beracun)",
        ],
        "causes": ["Defisiensi nutrisi", "Gangguan pencernaan", "Kebosanan", "Stres", "Anemia", "Perilaku kompulsif"],
        "red_flags": ["Muntah setelah makan benda asing", "Konstipasi/susah BAB", "Lesu dan tidak nafsu makan (tanda obstruksi!)"],
        "treatment": [
            {"type": "medical", "priority": 1, "label": "Periksa ke dokter", "desc": "Cek darah untuk rule out defisiensi nutrisi, anemia, atau gangguan pencernaan."},
            {"type": "environment", "priority": 2, "label": "Amankan lingkungan", "desc": "Singkirkan benda berbahaya. Beri mainan kunyah yang aman."},
            {"type": "dietary", "priority": 3, "label": "Perbaiki diet", "desc": "Pastikan nutrisi lengkap. Tambah serat (sayur, pumpkin) untuk rasa kenyang."},
            {"type": "training", "priority": 4, "label": "Latihan leave it", "desc": "Ajari perintah tinggalkan untuk benda berbahaya."},
        ],
        "prevention": "Mainan kunyah aman, stimulasi cukup, nutrisi seimbang.",
        "vet_required": True,
    },
    "elimination_issues": {
        "name_id": "Masalah Buang Air",
        "species": ["dog", "cat", "rabbit"],
        "description": "Buang air di tempat yang tidak seharusnya, padahal sudah toilet trained.",
        "symptoms": [
            "Kencing di tempat tidur/tikar",
            "BAB di dalam rumah (padahal sudah terlatih)",
            "Menyemprot (spraying) pada dinding/furniture — khusus kucing",
            "Buang air saat ditinggal sendiri",
            "Defekasi di tempat yang tidak biasa",
        ],
        "causes": ["Medis: ISK, batu kemih, diabetes", "Stres", "Perubahan lingkungan", "Territorial marking", "Toilet tidak bersih (kucing)"],
        "red_flags": ["Darah dalam urin/feses", "Menengejan tanpa hasil", "Kencing sedikit-sedikit tapi sering"],
        "treatment": [
            {"type": "medical", "priority": 1, "label": "Periksa ke dokter", "desc": "Rule out medis dulu! Cek urin, feses, dan USG jika perlu."},
            {"type": "environment", "priority": 2, "label": "Atur lingkungan", "desc": "Kucing: 1 litter box per kucing + 1. Bersihkan tiap hari. Anjing: tingkatkan frekuensi jalan."},
            {"type": "management", "priority": 3, "label": "Buang noda benar", "desc": "Gunakan enzymatic cleaner untuk hapus bau. Jangan gunakan amonia (mirip bau urin)."},
            {"type": "stress", "priority": 4, "label": "Kurangi stres", "desc": "Feliway (kucing) atau Adaptil (anjing) diffuser. Rutinitas konsisten."},
        ],
        "prevention": "Rutinitas konsisten, litter box bersih, perhatian cukup.",
        "vet_required": True,
    },
    "excessive_vocalization": {
        "name_id": "Vokalisasi Berlebihan",
        "species": ["dog", "cat"],
        "description": "Menggonggong/mengeong terus-menerus tanpa sebab jelas.",
        "symptoms": [
            "Menggonggong setiap ada suara di luar",
            "Mengeong keras malam hari (kucing senior)",
            "Melolong saat ditinggal",
            "Vokalisasi saat makan",
            "Gonggongan kompulsif",
        ],
        "causes": ["Kebosanan", "Kurang stimulasi", "Kecemasan", "Penyakit (hipertiroid pada kucing)", "Disfungsi kognitif senior"],
        "red_flags": ["Vokalisasi disertai mondar-mandir (sakit)", "Vokalisasi malam pada kucing senior", "Tiba-tiba jadi vokal (check tyroid!)"],
        "treatment": [
            {"type": "medical", "priority": 1, "label": "Cek medis dulu", "desc": "Kucing: cek hipertiroid (terutama senior). Anjing: cek nyeri kronis."},
            {"type": "exercise", "priority": 2, "label": "Tambah stimulasi", "desc": "Anjing: tambah durasi jalan. Kucing: main interaktif 15 menit, 2x sehari."},
            {"type": "training", "priority": 3, "label": "Latihan diam", "desc": "Ajari command diam atau tenang. Beri treat saat diam."},
            {"type": "environment", "priority": 4, "label": "Kurangi pemicu", "desc": "Tutup tirai jika menggonggong karena lihat orang lewat. Putar white noise."},
        ],
        "vet_required": False,
    },
    "stereotypic_behavior": {
        "name_id": "Perilaku Stereotip",
        "species": ["rabbit", "hamster", "guinea_pig", "bird"],
        "description": "Gerakan berulang tanpa fungsi akibat lingkungan tidak sesuai atau stres kronis.",
        "symptoms": [
            "Berputar-putar di kandang (circling)",
            "Menggigit jeruji kandang terus-menerus (bar biting)",
            "Ayunan kepala berulang (weaving) — pada burung",
            "Melompat ke belakang (backflipping) — pada hamster",
            "Menjilat dinding kandang",
            "Mencabut bulu sendiri (feather plucking pada burung)",
        ],
        "causes": ["Kandang terlalu kecil", "Kurang stimulasi", "Sendirian (hewan sosial butuh teman)", "Stres kronis", "Diet tidak sesuai"],
        "red_flags": ["Melukai diri", "Menolak makan", "Berat badan turun signifikan"],
        "treatment": [
            {"type": "environment", "priority": 1, "label": "Perbesar kandang", "desc": "Kandang minimal 4x ukuran hewan. Sediakan area bermain terpisah."},
            {"type": "enrichment", "priority": 2, "label": "Pengayaan lingkungan", "desc": "Sembunyikan makanan (foraging), sediakan mainan kunyah, tunnel, hiding spot."},
            {"type": "social", "priority": 3, "label": "Teman (jika sosial)", "desc": "Kelinci, marmut, burung — jangan pelihara sendirian."},
            {"type": "dietary", "priority": 4, "label": "Perbaiki diet", "desc": "Pastikan serat cukup (hay untuk rabbit/guinea pig), variasi sayuran."},
        ],
        "prevention": "Kandang sesuai ukuran, stimulasi setiap hari, teman sosial.",
        "vet_required": False,
    },
    "play_behavior": {
        "name_id": "Masalah Perilaku Bermain",
        "species": ["dog", "cat", "ferret"],
        "description": "Perilaku bermain yang tidak tepat atau berlebihan.",
        "symptoms": [
            "Menggigit tangan/kaki saat bermain",
            "Terlalu kasar saat bermain dengan hewan lain",
            "Tidak bisa tenang setelah bermain",
            "Menggonggong/menerkam saat diajak main",
            "Play aggression (tiba-tiba jadi agresif saat bermain)",
        ],
        "causes": ["Tidak diajarkan bite inhibition", "Kelelahan", "Kurang sosialisasi", "Overstimulasi"],
        "treatment": [
            {"type": "training", "priority": 1, "label": "Ajarkan bite inhibition", "desc": "Bila menggigit tangan, teriak aduh! dan hentikan main 10-20 detik."},
            {"type": "management", "priority": 2, "label": "Atur waktu main", "desc": "Main 5-10 menit, break, lalu lanjut. Jangan sampai overstimulasi."},
            {"type": "redirection", "priority": 3, "label": "Alihkan ke mainan", "desc": "Sediakan mainan tali/tug toy. Jangan biarkan menggigit tangan manusia."},
        ],
        "vet_required": False,
    },
}


def analyze_behavior(species: str, symptoms: list[str], text: str) -> dict:
    """
    Analisis perilaku berdasarkan gejala yang diberikan.
    Mengembalikan kondisi yang paling cocok dengan gejala.
    """
    text_lower = text.lower()
    symptom_text = " ".join(s.lower() for s in symptoms) + " " + text_lower
    
    results = []
    for cat, condition in BEHAVIOR_CONDITIONS.items():
        # Check species compatibility
        if species not in condition["species"] and condition["species"] != ["all"]:
            # Heuristic: some conditions work across species
            if cat not in ["fear_phobia", "pica"]:
                pass  # Skip
        
        # Score based on symptom matches
        score = 0
        matched_symptoms = []
        
        for symptom in condition["symptoms"]:
            if any(word in symptom_text for word in symptom.lower().split()[:3]):
                score += 1
                matched_symptoms.append(symptom)
        
        if score > 0:
            results.append({
                "category": cat,
                "name": condition["name_id"],
                "match_score": score,
                "matched_symptoms": matched_symptoms[:3],
                "description": condition["description"],
                "red_flags": [rf for rf in condition.get("red_flags", []) 
                             if any(w in text_lower for w in rf.lower().split()[:3])],
                "treatment": condition["treatment"],
                "vet_required": condition.get("vet_required", False),
                "dangerous": condition.get("dangerous", False),
            })
    
    # Sort by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "matched_conditions": results[:3],
        "primary_condition": results[0] if results else None,
        "total_conditions_scored": len(results),
        "requires_vet": any(r.get("vet_required", False) for r in results[:3]) if results else False,
        "dangerous": any(r.get("dangerous", False) for r in results[:3]) if results else False,
    }
