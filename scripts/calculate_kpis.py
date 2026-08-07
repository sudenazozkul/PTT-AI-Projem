"""Doğrulanmış CSV verisinden günlük ve şube bazlı KPI dosyaları üretir."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.kpi import calculate_branch_summary, calculate_daily_kpis
from ptt_ai_projem.validation import validate_branch_data


def main() -> int:
    source_path = PROJECT_ROOT / "data" / "sube_performans.csv"
    daily_output = PROJECT_ROOT / "data" / "gunluk_kpi.csv"
    summary_output = PROJECT_ROOT / "data" / "sube_kpi_ozet.csv"

    try:
        raw_data = load_branch_data(source_path)
    except DataLoadError as error:
        print(f"[HATA] Dosya okunamadı: {error}")
        return 1

    validation = validate_branch_data(raw_data)
    if not validation.is_valid or validation.cleaned_data is None:
        for error in validation.errors:
            print(f"[HATA] {error}")
        print("KPI hesaplanmadı; önce veri hatalarını düzeltin.")
        return 1

    daily_kpis = calculate_daily_kpis(validation.cleaned_data)
    branch_summary = calculate_branch_summary(validation.cleaned_data)

    daily_kpis.to_csv(daily_output, index=False, encoding="utf-8-sig")
    branch_summary.to_csv(summary_output, index=False, encoding="utf-8-sig")

    print(f"[BASARILI] {len(daily_kpis)} günlük KPI kaydı oluşturuldu.")
    print(f"[BASARILI] {len(branch_summary)} şube özeti oluşturuldu.")
    print(f"Günlük KPI dosyası: {daily_output}")
    print(f"Şube özet dosyası: {summary_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
