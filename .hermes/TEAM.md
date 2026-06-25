# Tim Agent Pawnia — Ekosistem Satwa

**Project Lead:** Wins (`wins`)  
**Kanban board:** `pawnia`  
**Repo:** `projects/sobatpaws-ai`

## Struktur organisasi

```
                    Wins (PM / Project Lead)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ML Trainers         Mobile Devs        Backend Devs
   pawnia-ml-1         pawnia-mobile-1    pawnia-backend-1
   pawnia-ml-2         pawnia-mobile-2    pawnia-backend-2
                                           pawnia-backend-3
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                      AI Developers
                      pawnia-ai-1
                      pawnia-ai-2
                      pawnia-ai-3
```

## Aturan kerja

1. **Hanya Wins** yang assign task di board `pawnia`
2. Agent **tidak** mengambil task tanpa assignee = profil mereka
3. **Blocker** → komentar kanban + tag Wins
4. **Arsitektur** → Wins eskalasi ke `architect` (tim Naincode)
5. Tim Naincode (`backend`, `frontend`, dll.) **tidak** terganggu

## Setup Hermes profiles

```bash
chmod +x infra/hermes/setup-pawnia-profiles.sh
./infra/hermes/setup-pawnia-profiles.sh
hermes profile list | grep pawnia
```

## Chat dengan agent

```bash
export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
cd "/Users/winnerharry/Naincode AI Dept"
pawnia-ai-1 chat    # contoh — setelah profile dibuat
wins chat           # PM memimpin & assign
```
