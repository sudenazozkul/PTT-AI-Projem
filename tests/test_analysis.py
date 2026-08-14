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


if __name__ == "__main__":
    unittest.main()
