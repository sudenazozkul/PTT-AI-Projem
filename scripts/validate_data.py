"""Örnek CSV dosyasını terminalden doğrular."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.validation import validate_branch_data


def main() -> int:
    csv_path = PROJECT_ROOT / "data" / "sube_performans.csv"

    try:
        data = load_branch_data(csv_path)
    except DataLoadError as error:
        print(f"[HATA] Dosya okunamadı: {error}")
        return 1

    result = validate_branch_data(data)

    print(f"Kontrol edilen kayıt sayısı: {len(data)}")
    print(f"Kontrol edilen sütun sayısı: {len(data.columns)}")

    for warning in result.warnings:
        print(f"[UYARI] {warning}")

    if result.errors:
        for error in result.errors:
            print(f"[HATA] {error}")
        print(f"\nDoğrulama başarısız: {len(result.errors)} hata bulundu.")
        return 1

    print("[BASARILI] Veri seti kullanıma hazır.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
