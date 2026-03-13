import os
import json
import re
import requests
from google import genai
from google.genai import types
from datetime import datetime

# --- Configurare ---
ANM_PDF_URL = "https://www.meteoromania.ro/Upload-Produse/nivologie/nivologie.pdf"
OUTPUT_FILE = "date_nivologie.json"
GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = """
Din buletinul nivometeorologic atașat, extrage riscul de avalanșă pentru fiecare masiv montan menționat.
Returnează DOAR un JSON valid, fără text suplimentar, fără markdown, fără ```json```.
Structura exactă:
{
  "data_actualizare": "YYYY-MM-DD",
  "fagaras": {"peste_1800": 3, "sub_1800": 2},
  "bucegi": {"peste_1800": 3, "sub_1800": 2},
  "rodnei": {"peste_1800": 3, "sub_1800": 2},
  "calimani": {"peste_1800": 2, "sub_1800": 2},
  "bistritei": {"peste_1800": 2, "sub_1800": 2},
  "ceahlau": {"peste_1800": 2, "sub_1800": 2},
  "tarcu": {"peste_1800": 3, "sub_1800": 2},
  "godeanu": {"peste_1800": 3, "sub_1800": 2},
  "parang": {"peste_1800": 3, "sub_1800": 2},
  "sureanu": {"peste_1800": 3, "sub_1800": 2},
  "retezat": {"peste_1800": 3, "sub_1800": 2},
  "occidentali": {"peste_1800": 2, "sub_1800": 2},
  "apuseni": {"peste_1800": 2, "sub_1800": 2},
  "vladeasa": {"peste_1800": 2, "sub_1800": 2},
  "bihor": {"peste_1800": 2, "sub_1800": 2},
  "muntele_mare": {"peste_1800": 2, "sub_1800": 2},
  "gilau": {"peste_1800": 2, "sub_1800": 2},
  "semenic": {"peste_1800": 2, "sub_1800": 2},
  "iezer_papusa": {"peste_1800": 3, "sub_1800": 2},
  "hasmas": {"peste_1800": 2, "sub_1800": 2},
  "ciucas": {"peste_1800": 2, "sub_1800": 2},
  "baiului": {"peste_1800": 3, "sub_1800": 2},
  "postavaru": {"peste_1800": 3, "sub_1800": 2},
  "piatra_mare": {"peste_1800": 2, "sub_1800": 2},
  "penteleu": {"peste_1800": 2, "sub_1800": 2},
  "vrancei": {"peste_1800": 2, "sub_1800": 2},
  "piatra_craiului": {"peste_1800": 3, "sub_1800": 2},
  "leaota": {"peste_1800": 3, "sub_1800": 2},
  "cernei": {"peste_1800": 0, "sub_1800": 0}
}

Reguli:
- Niveluri: 0=necunoscut, 1=scăzut, 2=moderat, 3=însemnat, 4=ridicat, 5=foarte ridicat
- Dacă un masiv apare explicit în buletin, folosește valorile din text
- Dacă un masiv NU apare explicit, folosește cel mai apropiat geografic ca fallback:
  - piatra_craiului, leaota, iezer_papusa → fagaras/bucegi
  - godeanu, sureanu, retezat → tarcu/parang
  - bistritei, calimani → rodnei dacă diferă, altfel valoarea lor proprie
  - hasmas, ceahlau → valoarea lor sau orientali general
  - baiului, postavaru, piatra_craiului → bucegi
  - ciucas, piatra_mare, vrancei, penteleu → occidentali
  - semenic → occidentali
  - cernei → 0 dacă nu e menționat
- Valorile din structura de mai sus sunt EXEMPLE, nu valori reale — citește din document
"""


def download_pdf(url: str) -> bytes:
    print(f"[1/4] Descărcare PDF de la: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    print(f"      PDF descărcat cu succes ({len(response.content) / 1024:.1f} KB)")
    return response.content


def analyze_with_gemini(pdf_bytes: bytes, api_key: str) -> dict:
    print(f"[2/4] Inițializare Gemini ({GEMINI_MODEL})...")
    client = genai.Client(api_key=api_key)

    print("[3/4] Trimitere PDF la Gemini pentru analiză...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            PROMPT
        ]
    )

    raw_text = response.text.strip()
    print(f"      Răspuns primit ({len(raw_text)} caractere)")
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)
    return json.loads(raw_text)


def save_json(data: dict, filepath: str):
    print(f"[4/4] Salvare date în: {filepath}")
    data["timestamp_procesare"] = datetime.utcnow().isoformat() + "Z"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("      Salvat cu succes!")


def main():
    print("=" * 50)
    print("  Nivo Vision - Procesare Buletin Nivologic ANM")
    print("=" * 50)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY nu este setat!")

    try:
        pdf_bytes = download_pdf(ANM_PDF_URL)
        data = analyze_with_gemini(pdf_bytes, api_key)
        save_json(data, OUTPUT_FILE)

        print(f"\n✅ Procesare completă! Data: {data.get('data_actualizare', 'N/A')}")
        for masiv, valori in data.items():
            if isinstance(valori, dict) and "peste_1800" in valori:
                print(f"   - {masiv}: >{valori['peste_1800']} / <{valori['sub_1800']}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Eroare la descărcarea PDF-ului: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"\n❌ Eroare la parsarea JSON-ului de la Gemini: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Eroare neașteptată: {e}")
        raise


if __name__ == "__main__":
    main()
