"""Kural tabanlı analiz modülünün temel davranış testleri."""

import unittest

import pandas as pd

from ptt_ai_projem.analysis import (
    ANALYSIS_SOURCE_COLUMNS,
    AnalysisConfig,
    AnalysisError,
    analyze_branches,
)
from ptt_ai_projem.recommendations import create_recommendations


class AnalysisTests(unittest.TestCase):
    @staticmethod
    def _delivery_time_frame(
        previous_times: list[float],
        recent_times: list[float],
        previous_deliveries: list[int],
        recent_deliveries: list[int],
    ) -> pd.DataFrame:
        times = previous_times + recent_times
        deliveries = previous_deliveries + recent_deliveries
        dates = pd.date_range("2026-01-01", periods=len(times), freq="D")
        return pd.DataFrame({
            "tarih": dates,
            "sube_kodu": "S001",
            "sube_adi": "Test Subesi",
            "il": "Ankara",
            "ilce": "Cankaya",
            "sube_tipi": "Merkez",
            "kabul_edilen": deliveries,
            "teslim_edilen": deliveries,
            "geciken": 0,
            "iade_edilen": 0,
            "ortalama_teslim_suresi": times,
            "toplam_personel": 10,
            "dagitici_sayisi": 5,
            "sikayet_sayisi": 0,
            "toplam_gelir": 1000.0,
            "izinli_personel": 0,
            "hava_durumu": "Acik",
            "fazla_mesai_saati": 0,
        })

    def test_missing_columns_are_reported(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "gerekli sütunlar eksik"):
            analyze_branches(pd.DataFrame({"sube_kodu": ["A"]}))

    def test_empty_valid_frame_has_no_findings(self) -> None:
        self.assertEqual(
            analyze_branches(pd.DataFrame(columns=sorted(ANALYSIS_SOURCE_COLUMNS))),
            [],
        )

    def test_every_finding_gets_a_recommendation(self) -> None:
        data = pd.read_csv("data/sube_performans.csv", encoding="utf-8-sig")
        findings = analyze_branches(data, AnalysisConfig())
        self.assertTrue(findings)
        self.assertEqual(len(create_recommendations(findings)), len(findings))

    def test_delivery_time_change_is_weighted_by_delivered_volume(self) -> None:
        previous_times = [1.0] * 30
        recent_times = [1.2] * 15 + [1.0] * 15
        previous_deliveries = [100] * 30
        recent_deliveries = [1] * 15 + [100] * 15
        data = self._delivery_time_frame(
            previous_times,
            recent_times,
            previous_deliveries,
            recent_deliveries,
        )

        simple_change = (
            pd.Series(recent_times).mean() / pd.Series(previous_times).mean() - 1
        )
        self.assertGreater(simple_change, AnalysisConfig().period_change_ratio)

        findings = analyze_branches(data)
        self.assertNotIn(
            "delivery_time_increase", {finding.rule_id for finding in findings}
        )

    def test_delivery_time_finding_reports_weighted_period_averages(self) -> None:
        data = self._delivery_time_frame(
            previous_times=[1.0] * 30,
            recent_times=[1.3] * 15 + [1.1] * 15,
            previous_deliveries=[100] * 30,
            recent_deliveries=[100] * 15 + [300] * 15,
        )

        findings = analyze_branches(data)
        finding = next(
            item for item in findings if item.rule_id == "delivery_time_increase"
        )

        self.assertEqual(finding.evidence["onceki_30_gun"], 1.0)
        self.assertEqual(finding.evidence["son_30_gun"], 1.15)
        self.assertEqual(finding.evidence["degisim_pct"], 15.0)


if __name__ == "__main__":
    unittest.main()
