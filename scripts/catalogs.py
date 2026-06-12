# -*- coding: utf-8 -*-
"""
Seed catalogs for the Sobatpaws data-generation pipeline.

This module is PURE DATA (no logic). It holds:
  * CATEGORY_IDS    -> stable id per category slug (matches data/categories.json)
  * TARGETS         -> how many leaf taxa to generate per category
  * TAXA            -> base species + modifier specs that get combinatorially
                       expanded into leaf taxa (ras / sub-ras / morph / warna)
  * CLINICAL        -> per-category disease vocabulary (each disease carries its
                       diagnostics, a first-line treatment, and candidate products)

The generator (generate_dataset.py) consumes this to emit schema-conformant rows.
All vocab values for enum-typed columns are kept inside the DBML enum domains.
"""

# Stable category ids — MUST match insertion order in data/categories.json
CATEGORY_IDS = {
    "dog": 1,
    "cat": 2,
    "rabbit": 3,
    "hamster": 4,
    "poultry": 5,
    "fish": 6,
    "reptile": 7,
    "amphibian": 8,
    "ferret": 9,
    "guinea_pig": 10,
}

# Per-category leaf-taxon targets.
# Default medium (~2.4k ras) untuk dataset klinis ~500k baris total.
# Untuk dataset taksonomi besar (jutaan baris), set TARGETS_LARGE via --taxonomy large.
TARGETS = {
    "dog": 400,
    "cat": 500,
    "poultry": 400,
    "rabbit": 90,
    "hamster": 50,
    "fish": 600,
    "reptile": 700,
    "amphibian": 30,
    "ferret": 25,
    "guinea_pig": 40,
}

TARGETS_LARGE = {
    "dog": 2500,
    "cat": 3500,
    "poultry": 3000,
    "rabbit": 600,
    "hamster": 400,
    "fish": 4000,
    "reptile": 15000,
    "amphibian": 200,
    "ferret": 100,
    "guinea_pig": 200,
}

# How many master diseases each leaf is paired with, and the medical fan-out.
# 6 diseases x 2 diagnostics x 2 products = 24 matrix rows per leaf taxon.
DISEASES_PER_TAXON = 6
DIAGNOSTICS_PER_DISEASE = 2
PRODUCTS_PER_DISEASE = 2

# ---------------------------------------------------------------------------
# Shared modifier pools
# ---------------------------------------------------------------------------

BALL_PYTHON_MORPHS = [
    "Pastel", "Spider", "Enchi", "Albino", "Piebald", "Banana", "Axanthic",
    "Lesser", "Cinnamon", "Mojave", "Clown", "Pinstripe", "Yellow Belly",
    "Fire", "Ghost", "Champagne", "Black Pastel", "Leopard", "Orange Dream",
    "Vanilla", "GHI", "Hypo", "Coral Glow", "Sable",
]
LEOPARD_GECKO_MORPHS = [
    "Tremper Albino", "Bell Albino", "Rainwater Albino", "Eclipse", "Blizzard",
    "Black Night", "Lemon Frost", "Tangerine", "Mack Snow", "Super Snow",
    "Enigma", "Murphy Patternless", "Bold Stripe", "Carrot Tail", "Giant",
    "Hypo", "Hyper Xanthic", "Jungle", "Aberrant", "Diablo Blanco",
    "White and Yellow", "Bandit", "Sunglow", "Raptor",
]
BEARDED_DRAGON_MORPHS = [
    "Classic", "Hypo", "Leatherback", "Silkback", "Translucent", "Witblits",
    "Zero", "Wero", "Dunner", "Paradox", "Citrus", "Tiger", "Red", "Orange",
    "Yellow", "Sandfire", "Sunburst", "German Giant", "Genetic Stripe",
    "Snow", "Blue Bar", "Smoothie", "Het Hypo", "Hypo Trans",
]
CORN_SNAKE_MORPHS = [
    "Amelanistic", "Anerythristic", "Snow", "Blood Red", "Caramel", "Lavender",
    "Charcoal", "Hypo", "Ghost", "Butter", "Opal", "Pewter", "Motley",
    "Striped", "Tessera", "Scaleless", "Sunkissed", "Diffused", "Cinder",
    "Kastanie", "Lava", "Plasma", "Fluorescent Orange", "Palmetto",
]
CRESTED_GECKO_MORPHS = [
    "Flame", "Harlequin", "Pinstripe", "Dalmatian", "Tiger", "Brindle",
    "Tricolor", "Lilly White", "Axanthic", "Halloween", "Phantom",
    "Cappuccino", "Patternless", "Extreme Harlequin", "Quad Stripe",
    "Creamsicle", "Red Base", "Yellow Base", "Olive", "White Wall",
    "Super Dalmatian", "Empty Back", "Partial Pin", "Full Pin",
]
RETIC_PYTHON_MORPHS = [
    "Tiger", "Super Tiger", "Albino", "Platinum", "Genetic Stripe", "Motley",
    "Anery", "Sunfire", "Citron", "Goldenchild", "Phantom", "Ivory",
    "Purple Albino", "Lavender Albino", "Pied", "Caramel", "Anthrax",
    "Titanium", "Mocha", "Jaguar", "Marble", "Calico", "Dwarf", "Het Albino",
]
SULCATA_MORPHS = [
    "Normal", "Ivory", "Hypo", "Albino", "Caramel", "High White",
    "Pyramiding-Free", "Smooth", "Marginated High", "Split-scute", "Highyellow",
    "Pastel", "Snow", "Anery", "Leucistic", "Patternless", "Sunburst",
    "Goldenrod", "Cream", "Ghost", "Banded", "Het Ivory", "Captive-bred F1",
    "Wild Type",
]
GREEN_IGUANA_MORPHS = [
    "Green", "Blue Axanthic", "Red", "Albino", "Hypo", "Crimson", "Snow",
    "T+ Albino", "Leucistic", "Sunburst", "Flame", "Tangerine", "High Red",
    "Purple", "Lemon", "Ghost", "Pastel", "Pied", "Stripe", "Banded",
    "Het Albino", "Adult Phase", "Hatchling Phase", "Wild Type",
]

CAT_COLOR_CODES = [
    "Solid White", "Solid Black", "Solid Blue", "Solid Red", "Solid Cream",
    "Solid Chocolate", "Solid Lilac", "Solid Cinnamon", "Solid Fawn",
    "Bicolor Black", "Bicolor Blue", "Bicolor Red", "Calico", "Dilute Calico",
    "Tortoiseshell", "Blue-Cream", "Chocolate Tortie", "Mackerel Tabby Brown",
    "Mackerel Tabby Silver", "Classic Tabby Brown", "Classic Tabby Silver",
    "Ticked Tabby", "Spotted Tabby", "Patched Tabby", "Seal Point",
    "Blue Point", "Chocolate Point", "Lilac Point", "Flame Point",
    "Cream Point", "Seal Lynx Point", "Blue Lynx Point", "Tortie Point",
    "Smoke Black", "Smoke Blue", "Shaded Silver", "Shaded Golden",
    "Chinchilla Silver", "Chinchilla Golden", "Tuxedo", "Van Bicolor",
    "Harlequin", "Mitted Seal", "Mitted Blue", "Sepia Brown", "Mink Natural",
    "Mink Champagne", "Mink Blue", "Mink Platinum", "Cameo Smoke",
    "Shell Cameo", "Tortie Smoke", "Blue Smoke", "Golden Tabby", "Ebony",
    "Chestnut", "Buff", "Apricot Tabby", "Caramel", "Cinnamon Silver",
    "Fawn Tabby", "Lavender", "Chocolate Smoke", "Lilac Lynx Point",
    "Chocolate Lynx Point", "Red Mackerel Tabby", "Brown Patched Tabby",
    "Silver Patched Tabby", "Blue Patched Tabby", "Cream Tabby",
    "Black Smoke Tabby", "Silver Shaded Point",
]

DOG_VARIANTS = [
    "Toy", "Miniature", "Standard", "Medium", "Black", "Yellow", "Chocolate",
    "Golden", "Cream", "Apricot", "Red", "Sable", "Brindle", "Pied", "Merle",
    "Blue Merle", "Tricolor", "Black & Tan", "Black & White", "Fawn", "Liver",
    "White", "Tan", "Silver", "Blue", "Wirehaired", "Smooth Coat", "Long Coat",
    "Curly Coat", "Parti",
]

CHICKEN_TYPES = ["Standard", "Bantam"]
CHICKEN_COLORS = [
    "White", "Black", "Buff", "Blue", "Splash", "Partridge", "Silver Laced",
    "Gold Laced", "Barred", "Lavender", "Mottled", "Columbian",
]
LOVEBIRD_MUTATIONS = [
    "Lutino", "Albino", "Biola", "Opaline", "Parblue", "Pastel", "Violet",
    "Dark Factor", "Cinnamon", "Fallow", "Euwing", "Pied", "Ino", "Sable",
    "Greywing", "Dilute",
]
BUDGIE_MUTATIONS = [
    "Spangle", "Opaline", "Cinnamon", "Lutino", "Albino", "Lacewing",
    "Pied Dominant", "Pied Recessive", "Greywing", "Clearwing", "Violet",
    "Cobalt", "Mauve", "Yellowface", "Dark Factor", "Texas Clearbody",
    "Saddleback", "Spangle Double Factor",
]
CANARY_COLORS = [
    "Red Intensive", "Yellow Shaded", "White Dominant", "Bronze", "Isabel",
    "Agate", "Opal", "Mosaic", "Ivory", "Topaz",
]
PIGEON_COLORS = [
    "White", "Blue Bar", "Red Check", "Black", "Grizzle", "Andalusian",
    "Ash Red", "Indigo",
]
FINCH_MUTATIONS = [
    "Normal", "Pied", "Fawn", "White", "Black-cheek", "Yellow", "Silver",
    "Cream", "Chestnut Flanked", "Penguin",
]

FISH_GRADES = [
    "Grade A", "Grade AA", "Grade AAA", "Show Grade", "Breeder Grade",
    "Premium", "Standard", "Contest",
]

RABBIT_COLORS = [
    "Ruby-Eyed White", "Blue-Eyed White", "Black", "Blue", "Chocolate",
    "Lilac", "Chestnut Agouti", "Opal", "Lynx", "Chinchilla", "Otter",
    "Sable Point", "Siamese Sable", "Smoke Pearl", "Tortoise", "Orange",
    "Fawn", "Steel Grey", "Broken Black", "Broken Orange", "Castor",
    "Himalayan", "Harlequin", "Tan", "Chocolate Otter", "Blue Otter",
    "Sable Marten", "Smoke Pearl Marten", "Chinchilla Light", "Squirrel",
]
HAMSTER_COATS = ["Short Hair", "Long Hair (Angora)", "Satin", "Rex"]
HAMSTER_COLORS = [
    "Golden", "Banded", "Black", "Cream", "Sable", "Mottled", "Cinnamon",
    "Dove", "Sapphire", "Pearl", "Champagne", "Albino", "Umbrous", "Lilac",
    "Yellow", "Tortoiseshell", "Black-Eyed White", "Roan", "Dominant Spot",
    "Recessive Dapple",
]
GUINEA_PIG_COLORS = [
    "Self Black", "Self White", "Self Cream", "Agouti Golden", "Agouti Silver",
    "Dutch", "Brindle", "Roan", "Dalmatian", "Tortoiseshell", "Himalayan",
    "Magpie",
]
FERRET_COLORS = [
    "Sable", "Albino", "Cinnamon", "Chocolate", "Champagne", "Black",
    "Dark-Eyed White", "Silver", "Panda", "Blaze", "Mitt", "Roan",
]
AXOLOTL_MORPHS = [
    "Wild Type", "Leucistic", "Golden Albino", "White Albino", "Melanoid",
    "Copper", "GFP", "Mosaic", "Chimera", "Piebald", "Lavender", "Firefly",
]


def _combo(pool, max_r, variant_type):
    return {"mode": "combo", "pool": pool, "max_r": max_r, "variant_type": variant_type}


def _product(axes):
    return {"mode": "product", "axes": axes}


def _axis(pool, variant_type):
    return {"pool": pool, "variant_type": variant_type}


# ---------------------------------------------------------------------------
# TAXA — base species + modifier specs per category
# ---------------------------------------------------------------------------
# Each base: name, name_id, origin, size_class, weight (min,max), height(min,max)|None,
#            lifespan(min,max), temperament, coat_type, care_level, traits[], mod{}

TAXA = {
    "reptile": [
        {"name": "Ball Python", "name_id": "Ular Sanca Bola", "origin": "West Africa",
         "size_class": "medium", "weight": (1, 2.5), "height": None, "lifespan": (20, 30),
         "temperament": "Tenang, jinak, menggulung saat takut.", "coat_type": "Sisik halus",
         "care_level": "medium", "traits": [("respiratory_infection_risk", "moderate"), ("anorexia_tendency", "high")],
         "mod": _combo(BALL_PYTHON_MORPHS, 3, "morph")},
        {"name": "Leopard Gecko", "name_id": "Leopard Gecko", "origin": "South Asia",
         "size_class": "small", "weight": (0.045, 0.09), "height": None, "lifespan": (10, 20),
         "temperament": "Jinak, nokturnal, pemula friendly.", "coat_type": "Sisik bertotol",
         "care_level": "medium", "traits": [("mbd_risk", "high"), ("impaction_risk", "high")],
         "mod": _combo(LEOPARD_GECKO_MORPHS, 3, "morph")},
        {"name": "Bearded Dragon", "name_id": "Bearded Dragon", "origin": "Australia",
         "size_class": "medium", "weight": (0.3, 0.6), "height": None, "lifespan": (8, 14),
         "temperament": "Jinak, diurnal, interaktif.", "coat_type": "Sisik berduri",
         "care_level": "high", "traits": [("mbd_risk", "very_high"), ("uvb_dependency", "very_high")],
         "mod": _combo(BEARDED_DRAGON_MORPHS, 3, "morph")},
        {"name": "Corn Snake", "name_id": "Ular Jagung", "origin": "United States",
         "size_class": "medium", "weight": (0.5, 0.9), "height": None, "lifespan": (15, 23),
         "temperament": "Jinak, mudah dirawat, pemula friendly.", "coat_type": "Sisik halus",
         "care_level": "low", "traits": [("respiratory_infection_risk", "moderate"), ("scale_rot_risk", "moderate")],
         "mod": _combo(CORN_SNAKE_MORPHS, 3, "morph")},
        {"name": "Crested Gecko", "name_id": "Crested Gecko", "origin": "New Caledonia",
         "size_class": "small", "weight": (0.035, 0.055), "height": None, "lifespan": (15, 20),
         "temperament": "Arboreal, jinak, nokturnal.", "coat_type": "Kulit bertekstur",
         "care_level": "low", "traits": [("mbd_risk", "high"), ("tail_drop", "yes")],
         "mod": _combo(CRESTED_GECKO_MORPHS, 3, "morph")},
        {"name": "Reticulated Python", "name_id": "Ular Sanca Batik", "origin": "Southeast Asia",
         "size_class": "giant", "weight": (15, 75), "height": None, "lifespan": (20, 30),
         "temperament": "Cerdas, kuat, butuh handler berpengalaman.", "coat_type": "Sisik mengkilap",
         "care_level": "high", "traits": [("respiratory_infection_risk", "high"), ("size_hazard", "very_high")],
         "mod": _combo(RETIC_PYTHON_MORPHS, 3, "morph")},
        {"name": "Sulcata Tortoise", "name_id": "Kura-kura Sulcata", "origin": "Sahel Africa",
         "size_class": "large", "weight": (30, 100), "height": None, "lifespan": (50, 80),
         "temperament": "Herbivora, kuat menggali, jinak.", "coat_type": "Karapas bersisik",
         "care_level": "high", "traits": [("mbd_risk", "high"), ("pyramiding_risk", "high")],
         "mod": _combo(SULCATA_MORPHS, 3, "morph")},
        {"name": "Green Iguana", "name_id": "Iguana Hijau", "origin": "Central/South America",
         "size_class": "large", "weight": (1, 8), "height": None, "lifespan": (12, 20),
         "temperament": "Herbivora, bisa teritorial saat dewasa.", "coat_type": "Sisik berduri dorsal",
         "care_level": "high", "traits": [("mbd_risk", "very_high"), ("kidney_disease_risk", "high")],
         "mod": _combo(GREEN_IGUANA_MORPHS, 3, "morph")},
    ],

    "fish": [
        {"name": "Betta", "name_id": "Ikan Cupang", "origin": "Southeast Asia", "size_class": "toy",
         "weight": (0.002, 0.004), "height": None, "lifespan": (2, 4),
         "temperament": "Teritorial, jantan agresif.", "coat_type": "Sirip lebar warna-warni",
         "care_level": "low", "traits": [("labyrinth_breather", "yes"), ("fin_rot_risk", "high")],
         "mod": _product([
             _axis(["Halfmoon", "Crowntail", "Plakat", "Double Tail", "Over Halfmoon",
                    "Veiltail", "Delta", "Rosetail", "Halfmoon Plakat", "Spadetail"], "morph"),
             _axis(["Nemo", "Multicolor", "Avatar", "Copper", "Blue Rim", "Koi", "Galaxy",
                    "Black Orchid", "Dragon Scale", "Mustard Gas", "Marble", "Yellow"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Goldfish", "name_id": "Ikan Mas Koki", "origin": "China", "size_class": "small",
         "weight": (0.05, 0.5), "height": None, "lifespan": (10, 20),
         "temperament": "Damai, rakus, penghasil limbah tinggi.", "coat_type": "Sisik metalik",
         "care_level": "medium", "traits": [("swim_bladder_risk", "high"), ("ammonia_sensitivity", "high")],
         "mod": _product([
             _axis(["Oranda", "Ranchu", "Ryukin", "Black Moor", "Bubble Eye", "Tosakin",
                    "Comet", "Fantail", "Telescope", "Lionhead", "Pearlscale", "Celestial"], "morph"),
             _axis(["Red", "Red-White", "Calico", "Chocolate", "Blue", "Black", "Panda", "Tricolor"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Koi", "name_id": "Ikan Koi", "origin": "Japan", "size_class": "large",
         "weight": (1, 15), "height": None, "lifespan": (25, 60),
         "temperament": "Damai, jinak, ikan kolam.", "coat_type": "Pola warna khas",
         "care_level": "high", "traits": [("khv_risk", "high"), ("parasite_risk", "high")],
         "mod": _product([
             _axis(["Kohaku", "Sanke", "Showa", "Tancho", "Ogon", "Utsuri", "Bekko", "Asagi",
                    "Shusui", "Goshiki", "Kujaku", "Doitsu"], "pattern"),
             _axis(["Red", "White", "Black", "Yellow", "Platinum", "Orange", "Blue"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Guppy", "name_id": "Ikan Guppy", "origin": "South America", "size_class": "toy",
         "weight": (0.0005, 0.002), "height": None, "lifespan": (1, 3),
         "temperament": "Damai, mudah berkembang biak.", "coat_type": "Sirip warna-warni",
         "care_level": "low", "traits": [("ich_risk", "moderate")],
         "mod": _product([
             _axis(["Fantail", "Delta", "Veiltail", "Lyretail", "Swordtail", "Roundtail",
                    "Crowntail", "Halfmoon"], "morph"),
             _axis(["Albino Full Red", "Blue Grass", "Dragon", "Tuxedo", "Mosaic", "Half Black",
                    "Koi Red", "Moscow Blue", "Snakeskin", "Japan Blue"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Discus", "name_id": "Ikan Discus", "origin": "Amazon", "size_class": "small",
         "weight": (0.15, 0.25), "height": None, "lifespan": (10, 15),
         "temperament": "Damai tapi sensitif, butuh air bersih.", "coat_type": "Tubuh pipih bundar",
         "care_level": "high", "traits": [("water_quality_sensitivity", "very_high")],
         "mod": _product([
             _axis(["Pigeon Blood", "Snakeskin", "Leopard", "Solid", "Spotted"], "pattern"),
             _axis(["Red Turquoise", "Blue Diamond", "Marlboro Red", "Checkerboard",
                    "White Butterfly", "Yellow", "Cobalt"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Snakehead", "name_id": "Ikan Channa", "origin": "Asia", "size_class": "medium",
         "weight": (0.5, 3), "height": None, "lifespan": (8, 15),
         "temperament": "Predator, teritorial, air breather.", "coat_type": "Sisik tebal",
         "care_level": "medium", "traits": [("aggression", "high"), ("jumper", "yes")],
         "mod": _product([
             _axis(["Maru", "Barca", "Pulchra", "Aurantimaculata", "Andrao", "Bleheri",
                    "Stewartii", "Asiatica"], "morph"),
             _axis(["Blue", "Red", "Yellow Sentarum", "Orange", "Galaxy"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Flowerhorn", "name_id": "Ikan Louhan", "origin": "Malaysia", "size_class": "medium",
         "weight": (0.5, 1.2), "height": None, "lifespan": (8, 12),
         "temperament": "Agresif, interaktif, jenong khas.", "coat_type": "Tubuh tebal & nuchal hump",
         "care_level": "medium", "traits": [("aggression", "high"), ("head_growth", "yes")],
         "mod": _product([
             _axis(["Kamfa", "Kamalau", "Zhen Zhu", "Golden Base", "Thai Silk", "King Kamfa",
                    "SRD", "Bonsai"], "morph"),
             _axis(["Red", "Gold", "Silver", "Pearl", "Faded"], "color"),
             _axis(FISH_GRADES, "grade")])},
        {"name": "Arowana", "name_id": "Ikan Arwana", "origin": "Southeast Asia", "size_class": "large",
         "weight": (1, 6), "height": None, "lifespan": (10, 20),
         "temperament": "Predator, teritorial, ikan premium.", "coat_type": "Sisik besar mengkilap",
         "care_level": "high", "traits": [("drop_eye_risk", "moderate"), ("water_quality_sensitivity", "high")],
         "mod": _product([
             _axis(["Super Red", "Golden Crossback", "Silver", "Jardini", "Banjar Red", "Green",
                    "Blue Base", "Chili Red"], "morph"),
             _axis(["High Back", "24K", "Blood", "Orange", "Platinum"], "color"),
             _axis(FISH_GRADES, "grade")])},
    ],

    # Cat & dog bases are filled programmatically below from name lists.
    "cat": [],
    "dog": [],
    "poultry": [],
    "rabbit": [],
    "hamster": [],
    "amphibian": [
        {"name": "Axolotl", "name_id": "Axolotl", "origin": "Mexico", "size_class": "small",
         "weight": (0.06, 0.3), "height": None, "lifespan": (10, 15),
         "temperament": "Akuatik, neotenik, tenang.", "coat_type": "Kulit halus permeabel",
         "care_level": "high", "traits": [("water_temp_sensitivity", "very_high"), ("impaction_risk", "high")],
         "mod": _combo(AXOLOTL_MORPHS, 3, "morph")},
        {"name": "White's Tree Frog", "name_id": "Katak Pohon Dumpy", "origin": "Australia",
         "size_class": "small", "weight": (0.03, 0.12), "height": None, "lifespan": (10, 16),
         "temperament": "Tenang, nokturnal, arboreal.", "coat_type": "Kulit lembap",
         "care_level": "medium", "traits": [("obesity_risk", "high"), ("chytrid_risk", "moderate")],
         "mod": _combo(["Green", "Blue Phase", "Snowflake", "Mint", "Powder Blue",
                        "Albino", "Caramel", "High Blue", "Hypo", "Patternless"], 3, "morph")},
    ],
    "ferret": [
        {"name": "Ferret", "name_id": "Musang Ferret", "origin": "Europe", "size_class": "small",
         "weight": (0.7, 2), "height": None, "lifespan": (6, 10),
         "temperament": "Aktif, penasaran, suka tidur lama.", "coat_type": "Bulu pendek",
         "care_level": "high", "traits": [("insulinoma_risk", "very_high"), ("adrenal_disease_risk", "very_high")],
         "mod": _combo(FERRET_COLORS, 3, "color")},
    ],
    "guinea_pig": [
        {"name": "American Guinea Pig", "name_id": "Marmut Amerika", "origin": "South America",
         "size_class": "small", "weight": (0.7, 1.2), "height": None, "lifespan": (5, 8),
         "temperament": "Sosial, jinak, vokal.", "coat_type": "Bulu pendek halus",
         "care_level": "medium", "traits": [("vitamin_c_dependency", "very_high"), ("scurvy_risk", "high")],
         "mod": _combo(GUINEA_PIG_COLORS, 2, "color")},
        {"name": "Abyssinian Guinea Pig", "name_id": "Marmut Abyssinian", "origin": "South America",
         "size_class": "small", "weight": (0.7, 1.2), "height": None, "lifespan": (5, 7),
         "temperament": "Aktif, ramah, rosette coat.", "coat_type": "Rosette/whorl coat",
         "care_level": "medium", "traits": [("scurvy_risk", "high")],
         "mod": _combo(GUINEA_PIG_COLORS, 2, "color")},
        {"name": "Peruvian Guinea Pig", "name_id": "Marmut Peruvian", "origin": "South America",
         "size_class": "small", "weight": (0.7, 1.2), "height": None, "lifespan": (5, 7),
         "temperament": "Bulu panjang, butuh grooming.", "coat_type": "Long silky coat",
         "care_level": "high", "traits": [("scurvy_risk", "high"), ("grooming_need", "high")],
         "mod": _combo(GUINEA_PIG_COLORS, 2, "color")},
    ],
}

# ---- Build cat bases (breed list x color codes) ----
CAT_BREEDS = [
    ("Persian", "Persia", "Iran", "medium"), ("Maine Coon", "Maine Coon", "United States", "large"),
    ("Siamese", "Siam", "Thailand", "small"), ("British Shorthair", "British Shorthair", "United Kingdom", "medium"),
    ("Ragdoll", "Ragdoll", "United States", "large"), ("Scottish Fold", "Scottish Fold", "Scotland", "medium"),
    ("Sphynx", "Sphynx", "Canada", "medium"), ("Bengal", "Bengal", "United States", "medium"),
    ("Abyssinian", "Abyssinian", "Ethiopia", "small"), ("Birman", "Birman", "Myanmar", "medium"),
    ("Burmese", "Burma", "Myanmar", "small"), ("Russian Blue", "Russian Blue", "Russia", "medium"),
    ("Norwegian Forest", "Hutan Norwegia", "Norway", "large"), ("Oriental Shorthair", "Oriental Shorthair", "Thailand", "small"),
    ("Devon Rex", "Devon Rex", "United Kingdom", "small"), ("Cornish Rex", "Cornish Rex", "United Kingdom", "small"),
    ("American Shorthair", "American Shorthair", "United States", "medium"), ("Exotic Shorthair", "Exotic Shorthair", "United States", "medium"),
    ("Himalayan", "Himalaya", "United States", "medium"), ("Tonkinese", "Tonkinese", "Canada", "small"),
    ("Egyptian Mau", "Egyptian Mau", "Egypt", "small"), ("Ocicat", "Ocicat", "United States", "medium"),
    ("Savannah", "Savannah", "United States", "large"), ("Munchkin", "Munchkin", "United States", "small"),
    ("Manx", "Manx", "Isle of Man", "medium"), ("Turkish Angora", "Angora Turki", "Turkey", "small"),
    ("Turkish Van", "Turkish Van", "Turkey", "medium"), ("Selkirk Rex", "Selkirk Rex", "United States", "medium"),
    ("LaPerm", "LaPerm", "United States", "small"), ("Chartreux", "Chartreux", "France", "medium"),
    ("Korat", "Korat", "Thailand", "small"), ("Singapura", "Singapura", "Singapore", "toy"),
    ("Somali", "Somali", "Somalia", "small"), ("Balinese", "Bali", "United States", "small"),
    ("Snowshoe", "Snowshoe", "United States", "medium"), ("Bombay", "Bombay", "United States", "small"),
    ("American Curl", "American Curl", "United States", "small"), ("American Bobtail", "American Bobtail", "United States", "medium"),
    ("Japanese Bobtail", "Japanese Bobtail", "Japan", "small"), ("Pixiebob", "Pixiebob", "United States", "medium"),
    ("Ragamuffin", "Ragamuffin", "United States", "large"), ("Nebelung", "Nebelung", "United States", "medium"),
    ("Siberian", "Siberia", "Russia", "large"), ("Burmilla", "Burmilla", "United Kingdom", "small"),
    ("Havana Brown", "Havana Brown", "United Kingdom", "small"), ("Lykoi", "Lykoi", "United States", "small"),
    ("Peterbald", "Peterbald", "Russia", "small"), ("Khao Manee", "Khao Manee", "Thailand", "small"),
    ("Toyger", "Toyger", "United States", "medium"), ("Chausie", "Chausie", "Egypt", "large"),
]
for _n, _nid, _origin, _size in CAT_BREEDS:
    TAXA["cat"].append({
        "name": _n, "name_id": _nid, "origin": _origin, "size_class": _size,
        "weight": (3, 7), "height": (20, 38), "lifespan": (12, 18),
        "temperament": "Mandiri, teritorial, hewan pendamping populer.",
        "coat_type": "Bervariasi sesuai ras", "care_level": "medium",
        "traits": [("grooming_need", "moderate")],
        "mod": _product([_axis(CAT_COLOR_CODES, "color")]),
    })

# ---- Build dog bases (purebreds + designer crosses) x variant pool ----
DOG_PUREBREDS = [
    "Golden Retriever", "Labrador Retriever", "German Shepherd", "French Bulldog", "Pug",
    "Poodle", "Chihuahua", "Shih Tzu", "Rottweiler", "Dachshund", "Beagle", "Bulldog",
    "Yorkshire Terrier", "Boxer", "Siberian Husky", "Doberman Pinscher", "Great Dane",
    "Shiba Inu", "Border Collie", "Australian Shepherd", "Cavalier King Charles Spaniel",
    "Maltese", "Pomeranian", "Bernese Mountain Dog", "Cocker Spaniel", "Mastiff",
    "Saint Bernard", "Akita", "Samoyed", "Bichon Frise", "Shar Pei", "Chow Chow",
    "Basset Hound", "Bloodhound", "Newfoundland", "Weimaraner", "Vizsla", "Whippet",
    "Greyhound", "Dalmatian", "Pointer", "English Setter", "Irish Setter", "Brittany",
    "Papillon", "Pekingese", "Lhasa Apso", "Havanese", "Miniature Schnauzer",
    "Standard Schnauzer", "Giant Schnauzer", "Jack Russell Terrier", "Bull Terrier",
    "Staffordshire Bull Terrier", "American Pit Bull Terrier", "Cane Corso", "Boerboel",
    "Belgian Malinois", "Rhodesian Ridgeback", "Alaskan Malamute", "Pembroke Welsh Corgi",
    "Cardigan Welsh Corgi", "Australian Cattle Dog", "Shetland Sheepdog", "Old English Sheepdog",
    "Collie", "Brussels Griffon", "Italian Greyhound", "Borzoi", "Afghan Hound", "Basenji",
    "Boston Terrier", "Wire Fox Terrier", "West Highland White Terrier", "Scottish Terrier",
    "Cairn Terrier", "Airedale Terrier", "Soft Coated Wheaten Terrier", "Keeshond", "Pharaoh Hound",
]
DOG_CROSSES = [
    "Goldendoodle", "Labradoodle", "Maltipoo", "Cavapoo", "Yorkipoo", "Cockapoo",
    "Bernedoodle", "Aussiedoodle", "Sheepadoodle", "Schnoodle", "Pomsky", "Pomchi",
    "Puggle", "Chiweenie", "Cavachon", "Mal-Shi", "Shorkie", "Morkie", "Pomapoo",
    "Havapoo", "Bichpoo", "Frenchton", "Chug", "Jackapoo", "Springador", "Goberian",
    "Horgi", "Borador", "Boxweiler", "Dorkie",
]
for _n in DOG_PUREBREDS:
    TAXA["dog"].append({
        "name": _n, "name_id": _n, "origin": "Various", "size_class": "medium",
        "weight": (5, 35), "height": (25, 60), "lifespan": (10, 15),
        "temperament": "Anjing pendamping/penjaga ras murni.",
        "coat_type": "Bervariasi", "care_level": "medium",
        "traits": [("trainability", "high")],
        "mod": _product([_axis(DOG_VARIANTS, "size")]),
    })
for _n in DOG_CROSSES:
    TAXA["dog"].append({
        "name": _n, "name_id": _n, "origin": "Designer Cross", "size_class": "medium",
        "weight": (4, 30), "height": (24, 58), "lifespan": (10, 16),
        "temperament": "Designer dog (crossbred) populer pasar hobi.",
        "coat_type": "Bervariasi (hybrid)", "care_level": "medium",
        "traits": [("hybrid_vigor", "yes")],
        "mod": _product([_axis(DOG_VARIANTS, "color")]),
    })

# ---- Build poultry/bird bases ----
CHICKEN_BREEDS = [
    "Silkie", "Cochin", "Brahma", "Polish", "Cemani", "Serama", "Sebright", "Wyandotte",
    "Plymouth Rock", "Orpington", "Leghorn", "Rhode Island Red", "Sussex", "Australorp",
    "Marans", "Faverolles", "Hamburg", "Ancona", "Araucana", "Easter Egger", "Dorking",
    "Sumatra", "Phoenix", "Frizzle", "Naked Neck",
]
for _n in CHICKEN_BREEDS:
    TAXA["poultry"].append({
        "name": f"{_n} Chicken", "name_id": f"Ayam {_n}", "origin": "Various", "size_class": "small",
        "weight": (0.5, 4), "height": None, "lifespan": (5, 10),
        "temperament": "Unggas darat, foraging aktif.", "coat_type": "Bulu bervariasi",
        "care_level": "medium", "traits": [("marek_risk", "moderate")],
        "mod": _product([_axis(CHICKEN_TYPES, "size"), _axis(CHICKEN_COLORS, "color")]),
    })
for _sp in ["Fischeri", "Personatus", "Roseicollis", "Nigrigenis", "Lilianae"]:
    TAXA["poultry"].append({
        "name": f"Lovebird {_sp}", "name_id": f"Lovebird {_sp}", "origin": "Africa", "size_class": "toy",
        "weight": (0.04, 0.06), "height": None, "lifespan": (10, 15),
        "temperament": "Aktif, sosial, vokal, populer kontes.", "coat_type": "Bulu warna cerah",
        "care_level": "medium", "traits": [("feather_plucking_risk", "moderate")],
        "mod": _combo(LOVEBIRD_MUTATIONS, 3, "color"),
    })
for _sp in ["English Budgerigar", "American Budgerigar"]:
    TAXA["poultry"].append({
        "name": _sp, "name_id": f"Parkit {_sp.split()[0]}", "origin": "Australia", "size_class": "toy",
        "weight": (0.03, 0.07), "height": None, "lifespan": (5, 10),
        "temperament": "Cerdas, vokal, sosial.", "coat_type": "Bulu warna-warni",
        "care_level": "medium", "traits": [("tumor_risk", "moderate")],
        "mod": _combo(BUDGIE_MUTATIONS, 2, "color"),
    })
TAXA["poultry"].append({
    "name": "Cockatiel", "name_id": "Burung Falk", "origin": "Australia", "size_class": "toy",
    "weight": (0.08, 0.12), "height": None, "lifespan": (15, 25),
    "temperament": "Jinak, ramah, bisa bersiul.", "coat_type": "Bulu abu-kuning",
    "care_level": "medium", "traits": [("night_fright", "moderate")],
    "mod": _combo(["Normal Grey", "Lutino", "Pied", "Pearl", "Cinnamon", "Whiteface",
                   "Albino", "Fallow", "Pastelface", "Yellowcheek", "Silver", "Emerald"], 2, "color"),
})
for _p in ["Yorkshire", "Norwich", "Lizard", "Gloster", "Border", "Fife", "Gibber Italicus", "Scotch Fancy"]:
    TAXA["poultry"].append({
        "name": f"{_p} Canary", "name_id": f"Kenari {_p}", "origin": "Europe", "size_class": "toy",
        "weight": (0.015, 0.03), "height": None, "lifespan": (10, 15),
        "temperament": "Burung kicau, postur kontes.", "coat_type": "Bulu halus",
        "care_level": "medium", "traits": [("air_sac_mite_risk", "moderate")],
        "mod": _combo(CANARY_COLORS, 2, "color"),
    })
for _b in ["Racing Homer", "Fantail", "Jacobin", "Pouter", "Tumbler", "King", "Modena",
           "Frillback", "Nun", "Oriental Frill"]:
    TAXA["poultry"].append({
        "name": f"{_b} Pigeon", "name_id": f"Merpati {_b}", "origin": "Various", "size_class": "small",
        "weight": (0.3, 0.7), "height": None, "lifespan": (8, 15),
        "temperament": "Merpati hias/balap.", "coat_type": "Bulu padat",
        "care_level": "medium", "traits": [("canker_risk", "moderate")],
        "mod": _combo(PIGEON_COLORS, 2, "color"),
    })
for _f in ["Zebra Finch", "Gouldian Finch", "Java Sparrow", "Bengalese Finch"]:
    TAXA["poultry"].append({
        "name": _f, "name_id": _f, "origin": "Various", "size_class": "toy",
        "weight": (0.01, 0.025), "height": None, "lifespan": (5, 10),
        "temperament": "Burung kecil sosial.", "coat_type": "Bulu halus",
        "care_level": "low", "traits": [("air_sac_mite_risk", "moderate")],
        "mod": _combo(FINCH_MUTATIONS, 2, "color"),
    })
TAXA["poultry"].append({
    "name": "Sun Conure", "name_id": "Burung Conure", "origin": "South America", "size_class": "small",
    "weight": (0.1, 0.13), "height": None, "lifespan": (15, 30),
    "temperament": "Vokal, ceria, butuh perhatian.", "coat_type": "Bulu kuning-oranye",
    "care_level": "high", "traits": [("feather_plucking_risk", "high")],
    "mod": _combo(["Normal", "Red Factor", "Pineapple", "Cinnamon", "Pied", "Lutino",
                   "Turquoise", "Suncheek", "Mint", "Yellowsided", "Dilute", "Fallow"], 2, "color"),
})

# ---- Build rabbit & hamster bases ----
RABBIT_BREEDS = [
    ("Netherland Dwarf", "toy"), ("Holland Lop", "small"), ("Lionhead", "small"), ("Rex", "medium"),
    ("Flemish Giant", "giant"), ("Mini Lop", "small"), ("English Angora", "medium"),
    ("French Lop", "large"), ("Dutch", "small"), ("Mini Rex", "small"), ("Polish", "toy"),
    ("English Lop", "large"), ("Himalayan", "small"), ("Californian", "medium"),
    ("New Zealand", "large"), ("Jersey Wooly", "toy"), ("Havana", "small"), ("Tan", "small"),
    ("Harlequin", "medium"), ("Satin", "medium"),
]
for _n, _size in RABBIT_BREEDS:
    TAXA["rabbit"].append({
        "name": _n, "name_id": _n, "origin": "Various", "size_class": _size,
        "weight": (0.5, 8), "height": None, "lifespan": (7, 12),
        "temperament": "Lagomorpha herbivora, gigi tumbuh terus.", "coat_type": "Bervariasi",
        "care_level": "medium", "traits": [("gi_stasis_risk", "high"), ("malocclusion_risk", "high")],
        "mod": _product([_axis(RABBIT_COLORS, "color")]),
    })
HAMSTER_SPECIES = [
    ("Syrian Hamster", "Syria", "small"), ("Roborovski Hamster", "Mongolia/China", "toy"),
    ("Winter White Hamster", "Siberia", "toy"), ("Campbell Hamster", "Central Asia", "toy"),
    ("Chinese Hamster", "China", "toy"),
]
for _n, _origin, _size in HAMSTER_SPECIES:
    TAXA["hamster"].append({
        "name": _n, "name_id": _n.replace("Hamster", "Hamster"), "origin": _origin, "size_class": _size,
        "weight": (0.02, 0.2), "height": None, "lifespan": (2, 3),
        "temperament": "Rodensia kecil nokturnal.", "coat_type": "Bervariasi",
        "care_level": "low", "traits": [("wet_tail_risk", "high"), ("diabetes_risk", "high")],
        "mod": _product([_axis(HAMSTER_COATS, "coat"), _axis(HAMSTER_COLORS, "color")]),
    })


# ---------------------------------------------------------------------------
# CLINICAL — per-category disease vocabulary
# ---------------------------------------------------------------------------
# Each disease:
#   slug, name, name_id, etiology, body_system, severity, contagious, zoonotic,
#   emergency, risk, prevalence,
#   diagnostics: [(slug, name, name_id, diagnostic_type), ...]   (>=2)
#   treatment:   (slug, name, name_id, treatment_type)
#   products:    [(sku, name, brand, kind, active_ingredient, form), ...]   (>=2)

def _dx(slug, name, name_id, dtype):
    return (slug, name, name_id, dtype)


def _tx(slug, name, name_id, ttype):
    return (slug, name, name_id, ttype)


def _pr(sku, name, brand, kind, ai, form):
    return (sku, name, brand, kind, ai, form)


# Reusable diagnostic / product fragments
DX_PHYS = _dx("dx-physical-exam", "Pemeriksaan Fisik", "Pemeriksaan Fisik", "physical_exam")
DX_BLOOD = _dx("dx-blood-panel", "Panel Darah Lengkap", "Panel Darah Lengkap", "blood_test")
DX_URINE = _dx("dx-urinalysis", "Urinalisis", "Urinalisis", "urinalysis")
DX_FECAL = _dx("dx-fecal", "Pemeriksaan Feses", "Pemeriksaan Feses", "fecal_exam")
DX_XRAY = _dx("dx-xray", "Radiografi (X-Ray)", "Radiografi (X-Ray)", "imaging_xray")
DX_USG = _dx("dx-ultrasound", "USG", "USG", "imaging_ultrasound")
DX_CYTO = _dx("dx-cytology", "Sitologi", "Sitologi", "cytology")
DX_PCR = _dx("dx-pcr", "PCR Molekular", "PCR Molekular", "pcr_molecular")
DX_CULTURE = _dx("dx-culture", "Kultur & Sensitivitas", "Kultur & Sensitivitas", "culture_sensitivity")
DX_SKIN = _dx("dx-skin-scraping", "Skin Scraping", "Kerokan Kulit", "skin_scraping")
DX_SEROLOGY = _dx("dx-serology", "Serologi/Antigen Test", "Tes Serologi/Antigen", "serology")
DX_HISTORY = _dx("dx-history", "Anamnesis", "Anamnesis (riwayat)", "history_taking")

TX_PHARMA = _tx("tx-pharma", "Terapi Farmakologis", "Terapi Farmakologis", "pharmacological")
TX_SUPPORT = _tx("tx-support", "Perawatan Suportif", "Perawatan Suportif", "supportive_care")
TX_DIET = _tx("tx-diet", "Manajemen Diet", "Manajemen Diet", "dietary")
TX_SURGERY = _tx("tx-surgery", "Tindakan Bedah", "Tindakan Bedah", "surgical")
TX_PARASITE = _tx("tx-parasite", "Kontrol Parasit", "Kontrol Parasit", "parasite_control")
TX_FLUID = _tx("tx-fluid", "Terapi Cairan", "Terapi Cairan", "fluid_therapy")
TX_ENV = _tx("tx-env", "Manajemen Lingkungan", "Manajemen Lingkungan", "environmental_management")
TX_VACCINE = _tx("tx-vaccine", "Vaksinasi Preventif", "Vaksinasi Preventif", "preventive_vaccination")

PR_ABX = _pr("PR-AMOX", "Amoxicillin", "Generic", "medication", "Amoxicillin", "oral")
PR_ENRO = _pr("PR-ENRO", "Enrofloxacin", "Baytril", "medication", "Enrofloxacin", "injeksi")
PR_METRO = _pr("PR-METRO", "Metronidazole", "Generic", "medication", "Metronidazole", "oral")
PR_FLUID = _pr("PR-RL", "Ringer Lactate", "Generic", "medication", "Ringer Lactate", "IV")
PR_MAROP = _pr("PR-MAROP", "Maropitant", "Cerenia", "medication", "Maropitant", "injeksi")
PR_MELOX = _pr("PR-MELOX", "Meloxicam", "Metacam", "medication", "Meloxicam", "oral")
PR_ITRA = _pr("PR-ITRA", "Itraconazole", "Generic", "antiparasitic", "Itraconazole", "oral")
PR_IVER = _pr("PR-IVER", "Ivermectin", "Generic", "antiparasitic", "Ivermectin", "topikal")
PR_CALCIUM = _pr("PR-CAL", "Calcium + D3 Supplement", "RepCal", "supplement", "Calcium glukonat + D3", "oral")
PR_DIET_RX = _pr("PR-DIET", "Diet Resep Terapeutik", "Generic", "food_prescription", "Diet terkontrol", "oral")
PR_DISINF = _pr("PR-DISINF", "Disinfektan Kandang", "Generic", "disinfectant", "Benzalkonium chloride", "cair")
PR_VITC = _pr("PR-VITC", "Vitamin C", "Generic", "supplement", "Asam askorbat", "oral")
PR_SALEP = _pr("PR-KETO", "Salep Ketoconazole", "Generic", "medication", "Ketoconazole", "topikal")
PR_FURO = _pr("PR-FURO", "Furosemide", "Generic", "medication", "Furosemide", "oral")
PR_PROBIO = _pr("PR-PROBIO", "Probiotik", "Generic", "supplement", "Lactobacillus spp.", "oral")
PR_ANTIFUNGAL_BATH = _pr("PR-MALA", "Malaseb Shampoo", "Malaseb", "grooming", "Miconazole + Chlorhexidine", "topikal")
PR_WORMER = _pr("PR-PRAZI", "Praziquantel", "Generic", "antiparasitic", "Praziquantel", "oral")


def _disease(slug, name, name_id, etiology, body_system, severity, risk,
             diagnostics, treatment, products,
             contagious=False, zoonotic=False, emergency=False, prevalence=None):
    return {
        "slug": slug, "name": name, "name_id": name_id, "etiology": etiology,
        "body_system": body_system, "severity": severity, "risk": risk,
        "contagious": contagious, "zoonotic": zoonotic, "emergency": emergency,
        "prevalence": prevalence, "diagnostics": diagnostics, "treatment": treatment,
        "products": products,
    }


_MAMMAL_COMMON = [
    _disease("obesity", "Obesity", "Obesitas", "nutritional", "endocrine", "moderate", "high",
             [DX_PHYS, DX_BLOOD], TX_DIET, [PR_DIET_RX, PR_MELOX], prevalence=30),
    _disease("dental-disease", "Dental Disease", "Penyakit Gigi", "degenerative", "dental", "moderate", "high",
             [DX_PHYS, DX_XRAY], TX_SURGERY, [PR_ABX, PR_MELOX], prevalence=25),
    _disease("gastroenteritis", "Gastroenteritis", "Gastroenteritis", "infectious_bacterial", "digestive", "moderate", "moderate",
             [DX_PHYS, DX_FECAL], TX_SUPPORT, [PR_METRO, PR_PROBIO], contagious=True, prevalence=18),
    _disease("dermatitis", "Dermatitis", "Dermatitis", "infectious_bacterial", "integumentary", "mild", "moderate",
             [DX_SKIN, DX_CYTO], TX_PHARMA, [PR_SALEP, PR_ANTIFUNGAL_BATH], prevalence=20),
    _disease("ear-infection", "Otitis (Ear Infection)", "Infeksi Telinga", "infectious_bacterial", "auditory", "mild", "moderate",
             [DX_PHYS, DX_CYTO], TX_PHARMA, [PR_ABX, PR_SALEP], prevalence=15),
    _disease("parasitic-worms", "Intestinal Parasites", "Cacingan", "parasitic_internal", "digestive", "moderate", "high",
             [DX_FECAL, DX_HISTORY], TX_PARASITE, [PR_WORMER, PR_IVER], zoonotic=True, prevalence=28),
]

CLINICAL = {
    "dog": [
        _disease("dog-hip-dysplasia", "Hip Dysplasia", "Displasia Pinggul", "genetic_congenital",
                 "musculoskeletal", "severe", "high", [DX_PHYS, DX_XRAY], TX_SURGERY,
                 [PR_MELOX, PR_DIET_RX], prevalence=22),
        _disease("dog-parvo", "Canine Parvovirus", "Parvovirus (Parvo)", "infectious_viral",
                 "digestive", "critical", "high", [DX_SEROLOGY, DX_BLOOD], TX_SUPPORT,
                 [PR_FLUID, PR_MAROP], contagious=True, emergency=True, prevalence=12),
        _disease("dog-otitis", "Otitis Externa", "Otitis Eksterna", "infectious_bacterial",
                 "auditory", "moderate", "high", [DX_PHYS, DX_CYTO], TX_PHARMA,
                 [PR_ABX, PR_SALEP], prevalence=20),
        _disease("dog-demodicosis", "Demodicosis", "Demodekosis (Scabies)", "parasitic_external",
                 "integumentary", "moderate", "moderate", [DX_SKIN, DX_CYTO], TX_PARASITE,
                 [PR_IVER, PR_ANTIFUNGAL_BATH], prevalence=14),
        _disease("dog-gastric-dilatation", "Gastric Dilatation-Volvulus", "Kembung Lambung (GDV)",
                 "traumatic", "digestive", "critical", "moderate", [DX_PHYS, DX_XRAY], TX_SURGERY,
                 [PR_FLUID, PR_MAROP], emergency=True, prevalence=5),
        _disease("dog-leptospirosis", "Leptospirosis", "Leptospirosis", "infectious_bacterial",
                 "urinary", "severe", "moderate", [DX_BLOOD, DX_PCR], TX_PHARMA,
                 [PR_ABX, PR_FLUID], contagious=True, zoonotic=True, prevalence=6),
    ] + _MAMMAL_COMMON,

    "cat": [
        _disease("cat-flutd", "Feline Lower Urinary Tract Disease", "Gangguan Saluran Kemih (FLUTD)",
                 "idiopathic", "urinary", "severe", "high", [DX_URINE, DX_USG], TX_SUPPORT,
                 [PR_FLUID, PR_DIET_RX], emergency=True, prevalence=20),
        _disease("cat-ckd", "Chronic Kidney Disease", "Penyakit Ginjal Kronis (CKD)", "degenerative",
                 "urinary", "severe", "high", [DX_BLOOD, DX_USG], TX_DIET,
                 [PR_DIET_RX, PR_FURO], prevalence=30),
        _disease("cat-hcm", "Hypertrophic Cardiomyopathy", "Kardiomiopati Hipertrofik (HCM)",
                 "genetic_congenital", "cardiovascular", "severe", "high", [DX_USG, DX_XRAY], TX_PHARMA,
                 [PR_FURO, PR_MELOX], prevalence=15),
        _disease("cat-panleukopenia", "Feline Panleukopenia", "Panleukopenia", "infectious_viral",
                 "digestive", "critical", "high", [DX_SEROLOGY, DX_PCR], TX_SUPPORT,
                 [PR_FLUID, PR_MAROP], contagious=True, emergency=True, prevalence=8),
        _disease("cat-ringworm", "Dermatophytosis (Ringworm)", "Ringworm (Jamur Kulit)",
                 "infectious_fungal", "integumentary", "mild", "high", [DX_CULTURE, DX_CYTO], TX_PHARMA,
                 [PR_ITRA, PR_ANTIFUNGAL_BATH], contagious=True, zoonotic=True, prevalence=18),
        _disease("cat-uri", "Feline Upper Respiratory Infection", "ISPA Kucing (Flu Kucing)",
                 "infectious_viral", "respiratory", "moderate", "high", [DX_PHYS, DX_PCR], TX_SUPPORT,
                 [PR_ABX, PR_FLUID], contagious=True, prevalence=25),
    ] + _MAMMAL_COMMON,

    "rabbit": [
        _disease("rabbit-gi-stasis", "GI Stasis", "Stasis Saluran Cerna", "metabolic", "digestive",
                 "severe", "high", [DX_PHYS, DX_XRAY], TX_SUPPORT, [PR_FLUID, PR_PROBIO],
                 emergency=True, prevalence=30),
        _disease("rabbit-malocclusion", "Dental Malocclusion", "Maloklusi Gigi", "genetic_congenital",
                 "dental", "moderate", "high", [DX_PHYS, DX_XRAY], TX_SURGERY, [PR_MELOX, PR_DIET_RX],
                 prevalence=25),
        _disease("rabbit-snuffles", "Pasteurellosis (Snuffles)", "Snuffles (Pasteurella)",
                 "infectious_bacterial", "respiratory", "moderate", "high", [DX_PHYS, DX_CULTURE],
                 TX_PHARMA, [PR_ENRO, PR_ABX], contagious=True, prevalence=20),
        _disease("rabbit-ecuniculi", "E. cuniculi", "Encephalitozoon cuniculi", "parasitic_internal",
                 "nervous", "moderate", "moderate", [DX_SEROLOGY, DX_BLOOD], TX_PARASITE,
                 [PR_WORMER, PR_MELOX], zoonotic=True, prevalence=12),
        _disease("rabbit-flystrike", "Flystrike (Myiasis)", "Myiasis (Belatung)", "parasitic_external",
                 "integumentary", "critical", "moderate", [DX_PHYS, DX_HISTORY], TX_SUPPORT,
                 [PR_IVER, PR_FLUID], emergency=True, prevalence=8),
        _disease("rabbit-sore-hocks", "Pododermatitis (Sore Hocks)", "Pododermatitis (Sore Hocks)",
                 "environmental", "integumentary", "moderate", "moderate", [DX_PHYS, DX_CYTO], TX_PHARMA,
                 [PR_ABX, PR_MELOX], prevalence=15),
    ],

    "hamster": [
        _disease("hamster-wet-tail", "Wet Tail (Proliferative Ileitis)", "Wet Tail", "infectious_bacterial",
                 "digestive", "critical", "high", [DX_PHYS, DX_FECAL], TX_SUPPORT, [PR_METRO, PR_FLUID],
                 contagious=True, emergency=True, prevalence=22),
        _disease("hamster-diabetes", "Diabetes Mellitus", "Diabetes Melitus", "metabolic", "endocrine",
                 "severe", "high", [DX_URINE, DX_BLOOD], TX_DIET, [PR_DIET_RX, PR_VITC], prevalence=18),
        _disease("hamster-tumor", "Neoplasia", "Tumor/Neoplasia", "neoplastic", "systemic", "severe",
                 "moderate", [DX_PHYS, DX_CYTO], TX_SURGERY, [PR_MELOX, PR_ABX], prevalence=15),
        _disease("hamster-abscess", "Abscess", "Abses", "infectious_bacterial", "integumentary", "moderate",
                 "moderate", [DX_PHYS, DX_CYTO], TX_SURGERY, [PR_ABX, PR_MELOX], prevalence=14),
        _disease("hamster-mites", "Demodex Mites", "Tungau Demodex", "parasitic_external", "integumentary",
                 "mild", "moderate", [DX_SKIN, DX_CYTO], TX_PARASITE, [PR_IVER, PR_ANTIFUNGAL_BATH],
                 prevalence=12),
        _disease("hamster-cheek-pouch", "Cheek Pouch Impaction", "Impaksi Kantung Pipi", "traumatic",
                 "digestive", "moderate", "moderate", [DX_PHYS, DX_HISTORY], TX_SUPPORT, [PR_FLUID, PR_ABX],
                 prevalence=10),
    ],

    "poultry": [
        _disease("poultry-newcastle", "Newcastle Disease", "Tetelo (ND)", "infectious_viral", "respiratory",
                 "critical", "high", [DX_PHYS, DX_PCR], TX_VACCINE, [PR_DISINF, PR_FLUID],
                 contagious=True, emergency=True, prevalence=20),
        _disease("poultry-cocci", "Coccidiosis", "Koksidiosis (Berak Darah)", "parasitic_internal",
                 "digestive", "severe", "high", [DX_FECAL, DX_HISTORY], TX_PHARMA, [PR_METRO, PR_FLUID],
                 contagious=True, prevalence=28),
        _disease("poultry-crd", "Chronic Respiratory Disease", "CRD (Ngorok)", "infectious_bacterial",
                 "respiratory", "moderate", "high", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ENRO, PR_ABX],
                 contagious=True, prevalence=25),
        _disease("poultry-fowlpox", "Fowl Pox", "Cacar Unggas", "infectious_viral", "integumentary",
                 "moderate", "moderate", [DX_PHYS, DX_CYTO], TX_SUPPORT, [PR_DISINF, PR_VITC],
                 contagious=True, prevalence=15),
        _disease("poultry-egg-binding", "Egg Binding", "Egg Binding (Telur Tersangkut)", "metabolic",
                 "reproductive", "severe", "moderate", [DX_PHYS, DX_XRAY], TX_SUPPORT, [PR_CALCIUM, PR_FLUID],
                 emergency=True, prevalence=10),
        _disease("poultry-worms", "Helminthiasis", "Cacingan Unggas", "parasitic_internal", "digestive",
                 "moderate", "high", [DX_FECAL, DX_HISTORY], TX_PARASITE, [PR_WORMER, PR_IVER],
                 prevalence=24),
    ],

    "fish": [
        _disease("fish-ich", "Ichthyophthirius (Ich)", "White Spot (Ich)", "parasitic_external",
                 "integumentary", "severe", "high", [DX_PHYS, DX_CYTO], TX_ENV, [PR_DISINF, PR_METRO],
                 contagious=True, prevalence=30),
        _disease("fish-finrot", "Fin Rot", "Busuk Sirip", "infectious_bacterial", "integumentary",
                 "moderate", "high", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ENRO, PR_ABX],
                 contagious=True, prevalence=25),
        _disease("fish-dropsy", "Dropsy", "Dropsy (Sisik Nanas)", "infectious_bacterial", "systemic",
                 "critical", "moderate", [DX_PHYS, DX_HISTORY], TX_SUPPORT, [PR_ABX, PR_DISINF],
                 emergency=True, prevalence=12),
        _disease("fish-swimbladder", "Swim Bladder Disorder", "Gangguan Gelembung Renang", "metabolic",
                 "systemic", "moderate", "high", [DX_PHYS, DX_XRAY], TX_DIET, [PR_DIET_RX, PR_PROBIO],
                 prevalence=20),
        _disease("fish-velvet", "Velvet Disease", "Velvet (Karat)", "parasitic_external", "integumentary",
                 "severe", "moderate", [DX_PHYS, DX_CYTO], TX_ENV, [PR_DISINF, PR_METRO],
                 contagious=True, prevalence=15),
        _disease("fish-columnaris", "Columnaris", "Columnaris (Mulut Kapas)", "infectious_bacterial",
                 "integumentary", "severe", "moderate", [DX_CYTO, DX_CULTURE], TX_PHARMA, [PR_ABX, PR_DISINF],
                 contagious=True, prevalence=14),
    ],

    "reptile": [
        _disease("reptile-mbd", "Metabolic Bone Disease", "Penyakit Tulang Metabolik (MBD)", "nutritional",
                 "musculoskeletal", "severe", "very_high", [DX_PHYS, DX_XRAY], TX_SUPPORT,
                 [PR_CALCIUM, PR_DIET_RX], prevalence=35),
        _disease("reptile-ri", "Respiratory Infection", "Infeksi Pernapasan", "infectious_bacterial",
                 "respiratory", "severe", "high", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ENRO, PR_FLUID],
                 prevalence=22),
        _disease("reptile-stomatitis", "Infectious Stomatitis (Mouth Rot)", "Mouth Rot (Stomatitis)",
                 "infectious_bacterial", "dental", "moderate", "high", [DX_PHYS, DX_CYTO], TX_PHARMA,
                 [PR_ABX, PR_DISINF], prevalence=18),
        _disease("reptile-dysecdysis", "Dysecdysis (Shedding Problem)", "Gangguan Ganti Kulit", "environmental",
                 "integumentary", "mild", "high", [DX_PHYS, DX_HISTORY], TX_ENV, [PR_DISINF, PR_VITC],
                 prevalence=24),
        _disease("reptile-impaction", "Impaction", "Impaksi (Sumbatan Usus)", "traumatic", "digestive",
                 "severe", "high", [DX_PHYS, DX_XRAY], TX_SUPPORT, [PR_FLUID, PR_DIET_RX],
                 emergency=True, prevalence=20),
        _disease("reptile-parasites", "Internal Parasites", "Parasit Internal", "parasitic_internal",
                 "digestive", "moderate", "high", [DX_FECAL, DX_HISTORY], TX_PARASITE, [PR_WORMER, PR_METRO],
                 prevalence=26),
        _disease("reptile-shellrot", "Shell Rot", "Busuk Karapas", "infectious_bacterial", "integumentary",
                 "moderate", "moderate", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ABX, PR_DISINF],
                 prevalence=15),
    ],

    "amphibian": [
        _disease("amphibian-chytrid", "Chytridiomycosis", "Chytrid (Jamur Kulit)", "infectious_fungal",
                 "integumentary", "critical", "high", [DX_SKIN, DX_PCR], TX_PHARMA, [PR_ITRA, PR_ANTIFUNGAL_BATH],
                 contagious=True, emergency=True, prevalence=20),
        _disease("amphibian-reddleg", "Red Leg Syndrome", "Red Leg (Septicemia)", "infectious_bacterial",
                 "systemic", "critical", "high", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ENRO, PR_FLUID],
                 contagious=True, emergency=True, prevalence=15),
        _disease("amphibian-impaction", "Impaction", "Impaksi", "traumatic", "digestive", "severe",
                 "high", [DX_PHYS, DX_XRAY], TX_SUPPORT, [PR_FLUID, PR_DIET_RX], prevalence=18),
        _disease("amphibian-mbd", "Metabolic Bone Disease", "MBD", "nutritional", "musculoskeletal",
                 "severe", "high", [DX_PHYS, DX_XRAY], TX_SUPPORT, [PR_CALCIUM, PR_DIET_RX], prevalence=22),
        _disease("amphibian-edema", "Edema Syndrome", "Sindrom Edema", "metabolic", "systemic", "severe",
                 "moderate", [DX_PHYS, DX_BLOOD], TX_SUPPORT, [PR_FLUID, PR_FURO], prevalence=10),
        _disease("amphibian-parasites", "Parasitic Infection", "Infeksi Parasit", "parasitic_internal",
                 "digestive", "moderate", "moderate", [DX_FECAL, DX_CYTO], TX_PARASITE, [PR_WORMER, PR_METRO],
                 prevalence=16),
    ],

    "ferret": [
        _disease("ferret-insulinoma", "Insulinoma", "Insulinoma", "neoplastic", "endocrine", "severe",
                 "very_high", [DX_BLOOD, DX_USG], TX_SURGERY, [PR_DIET_RX, PR_MELOX], prevalence=25),
        _disease("ferret-adrenal", "Adrenal Disease", "Penyakit Adrenal", "neoplastic", "endocrine",
                 "severe", "very_high", [DX_USG, DX_BLOOD], TX_PHARMA, [PR_MELOX, PR_ABX], prevalence=30),
        _disease("ferret-ece", "Epizootic Catarrhal Enteritis", "ECE (Green Slime)", "infectious_viral",
                 "digestive", "moderate", "high", [DX_FECAL, DX_HISTORY], TX_SUPPORT, [PR_FLUID, PR_PROBIO],
                 contagious=True, prevalence=18),
        _disease("ferret-lymphoma", "Lymphoma", "Limfoma", "neoplastic", "hematologic", "severe",
                 "moderate", [DX_BLOOD, DX_CYTO], TX_PHARMA, [PR_MELOX, PR_ABX], prevalence=12),
        _disease("ferret-distemper", "Canine Distemper", "Distemper", "infectious_viral", "respiratory",
                 "critical", "moderate", [DX_SEROLOGY, DX_PCR], TX_VACCINE, [PR_FLUID, PR_ABX],
                 contagious=True, emergency=True, prevalence=6),
        _disease("ferret-gi-foreign", "GI Foreign Body", "Benda Asing Saluran Cerna", "traumatic",
                 "digestive", "severe", "high", [DX_XRAY, DX_PHYS], TX_SURGERY, [PR_FLUID, PR_MAROP],
                 emergency=True, prevalence=14),
    ],

    "guinea_pig": [
        _disease("gp-scurvy", "Scurvy (Vit C Deficiency)", "Scurvy (Kekurangan Vit C)", "nutritional",
                 "musculoskeletal", "severe", "very_high", [DX_PHYS, DX_HISTORY], TX_SUPPORT,
                 [PR_VITC, PR_DIET_RX], prevalence=30),
        _disease("gp-malocclusion", "Dental Malocclusion", "Maloklusi Gigi", "genetic_congenital", "dental",
                 "moderate", "high", [DX_PHYS, DX_XRAY], TX_SURGERY, [PR_MELOX, PR_DIET_RX], prevalence=24),
        _disease("gp-uri", "Upper Respiratory Infection", "ISPA Marmut", "infectious_bacterial",
                 "respiratory", "severe", "high", [DX_PHYS, DX_CULTURE], TX_PHARMA, [PR_ENRO, PR_FLUID],
                 contagious=True, prevalence=22),
        _disease("gp-bladder-stone", "Bladder Stones", "Batu Kandung Kemih", "metabolic", "urinary",
                 "severe", "moderate", [DX_URINE, DX_XRAY], TX_SURGERY, [PR_DIET_RX, PR_MELOX], prevalence=16),
        _disease("gp-ringworm", "Ringworm", "Ringworm", "infectious_fungal", "integumentary", "mild",
                 "moderate", [DX_CULTURE, DX_SKIN], TX_PHARMA, [PR_ITRA, PR_ANTIFUNGAL_BATH],
                 contagious=True, zoonotic=True, prevalence=14),
        _disease("gp-mites", "Mange Mites", "Tungau (Mange)", "parasitic_external", "integumentary",
                 "moderate", "high", [DX_SKIN, DX_CYTO], TX_PARASITE, [PR_IVER, PR_ANTIFUNGAL_BATH],
                 prevalence=20),
    ],
}

# Perkaya dengan katalog klinis diperluas (penyakit + gejala per penyakit)
try:
    from clinical_vocabulary import expand_clinical_catalog

    CLINICAL = expand_clinical_catalog(CLINICAL)
except ImportError:
    pass  # generate_dataset standalone tanpa expansion

# Penyakit tambahan dari knowledge base JSON (auto-sync)
try:
    from _kb_clinical_overlay import KB_CLINICAL_OVERLAY

    for _cat, _dis_list in KB_CLINICAL_OVERLAY.items():
        CLINICAL.setdefault(_cat, [])
        _existing = {d["slug"] for d in CLINICAL[_cat]}
        for _d in _dis_list:
            if _d["slug"] not in _existing:
                CLINICAL[_cat].append(_d)
                _existing.add(_d["slug"])
except ImportError:
    pass  # jalankan scripts/sync_catalogs_from_kb.py untuk overlay
