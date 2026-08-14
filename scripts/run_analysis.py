"""Doğrulanmış şube verisi için kural tabanlı analiz raporu üretir."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ptt_ai_projem.analysis import AnalysisError, analyze_branches
from ptt_ai_projem.data_loader import DataLoadError, load_branch_data
from ptt_ai_projem.recommendations import create_recommendations
from ptt_ai_projem.validation import validate_branch_data


def main() -> int:
    try:
        raw_data = load_branch_data(PROJECT_ROOT / "data" / "sube_performans.csv")
        validation = validate_branch_data(raw_data)
        if not validation.is_valid or validation.cleaned_data is None:
            print("[HATA] Veri doğrulama başarısız:")
            print("\n".join(validation.errors))
            return 1
        recommendations = create_recommendations(analyze_branches(validation.cleaned_data))
    except (DataLoadError, AnalysisError) as error:
        print(f"[HATA] {error}")
        return 1

    print(f"{len(recommendations)} kural tabanlı bulgu üretildi.\n")
    current_branch = None
    for item in recommendations:
        finding = item.finding
        if finding.branch_name != current_branch:
            current_branch = finding.branch_name
            print(f"## {current_branch}")
        print(f"Bulgu: {finding.detail}")
        print(f"Olası neden: {finding.possible_cause}")
        print(f"Öneri: {item.action}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
