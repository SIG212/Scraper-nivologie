# 🏔️ Nivo Vision — Automatizare Buletin Nivologic ANM

Sistem automat care descarcă zilnic buletinul nivologic de la ANM, îl analizează cu Gemini AI și salvează datele structurate în `date_nivologie.json`.

## 📁 Structura proiectului

```
├── .github/
│   └── workflows/
│       └── nivo_vision.yml     # Automatizarea GitHub Actions
├── nivo_vision.py              # Scriptul principal
├── requirements.txt            # Dependențe Python
├── date_nivologie.json         # Output generat automat (creat după prima rulare)
└── README.md
```

## ⚙️ Setup (o singură dată)

### 1. Obține un API Key Gemini
- Accesează [Google AI Studio](https://aistudio.google.com/apikey)
- Creează un API key gratuit

### 2. Adaugă secretul în GitHub
- Mergi la repository → **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret**
- Nume: `GEMINI_API_KEY`
- Valoare: cheia ta API

### 3. Activează GitHub Actions
- Mergi la tab-ul **Actions** din repository
- Dacă e dezactivat, click **Enable GitHub Actions**

## 🚀 Rulare

**Automată:** În fiecare zi la 08:00 UTC (10:00 ora României iarna, 11:00 vara)

**Manuală:**
- Mergi la **Actions** → **Actualizare Date Nivologice** → **Run workflow**

**Local:**
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="cheia_ta_aici"
python nivo_vision.py
```

## 📊 Formatul datelor (`date_nivologie.json`)

```json
{
  "data_actualizare": "2025-01-15",
  "sursa": "ANM - Administrația Națională de Meteorologie",
  "masive": [
    {
      "nume": "Bucegi",
      "risc_avalansa": 3,
      "descriere_risc": "Risc însemnat",
      "statii": [
        {
          "nume_statie": "Vf. Omu",
          "altitudine_m": 2505,
          "grosime_zapada_cm": 187,
          "observatii": "..."
        }
      ]
    }
  ],
  "timestamp_procesare": "2025-01-15T08:05:32Z"
}
```

## 🔧 Personalizare

Poți modifica `ANM_PDF_URL` în `nivo_vision.py` dacă ANM schimbă URL-ul PDF-ului.

Scala de risc avalanșă:
| Nivel | Descriere |
|-------|-----------|
| 1 | Risc redus |
| 2 | Risc limitat |
| 3 | Risc însemnat |
| 4 | Risc mare |
| 5 | Risc foarte mare |
