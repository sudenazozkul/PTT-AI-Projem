"""Doğrulanmış şube verisi için günlük KPI anomali raporu üretir."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.anomaly import AnomalyDetectionError, detect_anomalies
from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.validation import validate_branch_data


def main() -> int:
    try:
        raw_data = load_branch_data(PROJECT_ROOT / "data" / "sube_performans.csv")
        validation = validate_branch_data(raw_data)
        if not validation.is_valid or validation.cleaned_data is None:
            print("[HATA] Veri doğrulama başarısız:")
            print("\n".join(validation.errors))
            return 1
        anomalies = detect_anomalies(validation.cleaned_data)
    except (DataLoadError, AnomalyDetectionError) as error:
        print(f"[HATA] {error}")
        return 1

    print(f"{len(anomalies)} günlük KPI anomalisi bulundu.\n")
    for item in anomalies:
        print(
            f"{item.date:%d.%m.%Y} | {item.branch_name} | {item.metric_label} | "
            f"{item.severity.upper()}"
        )
        print(
            f"Gerçekleşen: {item.actual_value:.2f} | Olağan medyan: "
            f"{item.expected_value:.2f} | Anomali skoru: {item.anomaly_score:.2f}"
        )
        print(f"İnceleme: {item.suggested_check}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
