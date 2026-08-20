"""Entegrasyon katmanının mevcut Python modülleriyle çalıştığını doğrular."""

import unittest

from backend.service import (
    get_analysis,
    get_branch_detail,
    get_branches,
    get_comparison,
    get_metadata,
    get_methodology,
    get_overview,
)


class IntegrationServiceTests(unittest.TestCase):
    def test_overview_exposes_all_original_kpis(self) -> None:
        result = get_overview()
        self.assertGreater(result["metrics"]["toplam_gonderi"], 0)
        for key in (
            "teslim_basarisi_pct", "gecikme_orani_pct", "iade_orani_pct",
            "sikayet_orani_binde", "personel_verimliligi", "dagitici_is_yuku",
            "gonderi_basi_gelir", "ortalama_teslim_suresi",
        ):
            self.assertIn(key, result["metrics"])
        self.assertTrue(result["monthly"])
        self.assertIn("risk_branch", result["highlights"])

    def test_general_success_score_drives_ranking_and_highlights(self) -> None:
        result = get_overview()
        branches = result["branches"]
        scores = [branch["genel_basari_puani"] for branch in branches]

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(result["highlights"]["best_branch"]["sube_kodu"], branches[0]["sube_kodu"])
        self.assertEqual(result["highlights"]["risk_branch"]["sube_kodu"], branches[-1]["sube_kodu"])
        for branch in branches:
            self.assertAlmostEqual(
                sum(branch["genel_basari_katkilari"].values()),
                branch["genel_basari_puani"],
                places=2,
            )
            self.assertEqual(len(branch["genel_basari_alt_puanlari"]), 8)

    def test_general_success_reference_does_not_change_with_single_branch_filter(self) -> None:
        full = get_overview()
        branch = full["branches"][3]
        filtered = get_overview(branch_codes=[branch["sube_kodu"]])["branches"][0]

        self.assertEqual(filtered["genel_basari_puani"], branch["genel_basari_puani"])
        self.assertEqual(filtered["siralama"], branch["siralama"])

    def test_institution_monthly_trend_uses_weighted_institution_summary(self) -> None:
        result = get_overview(start_date="2026-01-01", end_date="2026-01-31")
        monthly = result["monthly"][0]

        self.assertEqual(monthly["teslim_basarisi_pct"], result["metrics"]["teslim_basarisi_pct"])
        self.assertEqual(monthly["gecikme_orani_pct"], result["metrics"]["gecikme_orani_pct"])
        self.assertEqual(monthly["ortalama_teslim_suresi"], result["metrics"]["ortalama_teslim_suresi"])

    def test_all_data_views_have_original_outputs(self) -> None:
        branches = get_branches()
        codes = [item["sube_kodu"] for item in branches[:4]]
        detail = get_branch_detail(codes[0])
        self.assertIsNotNone(detail)
        self.assertTrue(detail["trend"])
        self.assertTrue(detail["monthly"])
        comparison = get_comparison(codes)
        self.assertEqual(len(comparison["branches"]), 4)
        self.assertTrue(comparison["monthly"])
        analysis = get_analysis(branch_codes=[codes[0]])
        self.assertIn("anomalies", analysis)
        self.assertIn("affected_finding_branches", analysis["summary"])

    def test_metadata_and_methodology_are_traceable(self) -> None:
        self.assertEqual(get_metadata()["record_count"], 1800)
        methodology = get_methodology()
        self.assertEqual(len(methodology["kpi_formulas"]), 8)
        self.assertEqual(
            sum(item["weight_pct"] for item in methodology["kpi_formulas"]),
            100,
        )
        self.assertTrue(all(item["direction"] for item in methodology["kpi_formulas"]))
        self.assertEqual(methodology["anomaly"]["warning_threshold"], 3.5)
        self.assertIn("birleşik performans", methodology["scoring_note"])


if __name__ == "__main__":
    unittest.main()
