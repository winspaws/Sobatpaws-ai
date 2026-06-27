
import sys, os, json, glob, copy

LOCAL_CLINICAL = '/home/ubuntu/sobatpaws/data/clinical'
sys.path.insert(0, '/home/ubuntu/sobatpaws/scripts')

import expand_knowledge_base as ekb
import expand_other_species as eos

# Map species slug -> file name
slug_to_file = {
    'dog': 'diseases_dogs.json',
    'cat': 'diseases_cats.json',
    'rabbit': 'diseases_rabbits.json',
    'hamster': 'diseases_hamsters.json',
    'guinea_pig': 'diseases_guinea_pig.json',
    'ferret': 'diseases_ferret.json',
    'fish': 'diseases_fish.json',
    'reptile': 'diseases_reptiles.json',
    'amphibian': 'diseases_amphibian.json',
    'poultry': 'diseases_poultry.json',
    'exotic_others': 'diseases_exotic_others.json',
}

total_added = 0
total_diseases = 0

# Process dogs and cats from expand_knowledge_base
for slug, new_diseases in ekb.EXPANDED_DISEASES.items():
    fname = slug_to_file.get(slug)
    if not fname:
        print(f"SKIP {slug}: no file mapping")
        continue
    fpath = os.path.join(LOCAL_CLINICAL, fname)
    
    with open(fpath) as f:
        data = json.load(f)
    
    existing = data.get('diseases', [])
    existing_slugs = {d['slug'] for d in existing}
    
    added = 0
    for d in new_diseases:
        if d['slug'] not in existing_slugs:
            existing.append(d)
            added += 1
            existing_slugs.add(d['slug'])
    
    data['diseases'] = existing
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    total_added += added
    total_diseases += len(existing)
    print(f"{fname}: {len(existing)} diseases (+{added} new)")

# Process other species from expand_other_species
for fname, new_diseases in eos.EXPANSIONS.items():
    fpath = os.path.join(LOCAL_CLINICAL, fname)
    
    with open(fpath) as f:
        data = json.load(f)
    
    existing = data.get('diseases', [])
    existing_slugs = {d['slug'] for d in existing}
    
    added = 0
    for d in new_diseases:
        if d['slug'] not in existing_slugs:
            existing.append(d)
            added += 1
            existing_slugs.add(d['slug'])
    
    data['diseases'] = existing
    with open(fpath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    total_added += added
    total_diseases += len(existing)
    print(f"{fname}: {len(existing)} diseases (+{added} new)")

print(f"\n=== FINAL: {total_diseases} total diseases (+{total_added} new) ===")
assert total_diseases >= 200, f"Target 200+ not met: {total_diseases}"
