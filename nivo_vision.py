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
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"

PROMPT = """
Analizează acest buletin nivologic și extrage datele pentru TOATE masivele montane menționate.
Pentru fiecare masiv, extrage:
- numele masivului
- riscul de avalanșă (număr 1-5)
- descrierea riscului (ex: "Risc redus", "Risc limitat", "Risc însemnat", "Risc mare", "Risc foarte mare")
- grosimea stratului de zăpadă (în cm) la stațiile meteorologice menționate
- altitudinea stației (dacă este disponibilă)
- orice observații relevante despre condițiile nivologice

Returnează DOAR un JSON valid, fără text suplimentar, fără markdown, fără ```json```.
Structura JSON trebuie să fie:
{
  "data_actualizare": "YYYY-MM-DD",
  "sursa": "ANM - Administrația Națională de Meteorologie",
  "masive": [
    {
      "nume": "Numele Masivului",
      "risc_avalansa": 3,
      "descriere_risc": "Risc însemnat",
      "statii": [
        {
          "nume_statie": "Numele Stației",
          "altitudine_m": 2505,
          "grosime_zapada_cm": 187,
          "observatii": "Text observații dacă există"
        }
      ]
    }
  ]
}
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

        print(f"\n✅ Procesare completă! Masive extrase: {len(data.get('masive', []))}")
        for masiv in data.get("masive", []):
            print(f"   - {masiv.get('nume')}: Risc {masiv.get('risc_avalansa')} ({masiv.get('descriere_risc')})")

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
