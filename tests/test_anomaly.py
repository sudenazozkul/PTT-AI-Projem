"""Günlük KPI anomali tespitinin temel davranış testleri."""

import unittest

import pandas as pd

from ptt_ai_projem.anomaly import (
    ANOMALY_SOURCE_COLUMNS,
    AnomalyConfig,
    AnomalyDetectionError,
    detect_anomalies,
)


class AnomalyTests(unittest.TestCase):
    @staticmethod
    def _data_with_known_delay_anomaly() -> pd.DataFrame:
        rows = []
        for day in range(40):
            delayed = 5 + day % 3
            if day == 39:
                delayed = 40
            rows.append({
                "tarih": f"2026-01-{day + 1:02d}" if day < 31 else f"2026-02-{day - 30:02d}",
                "sube_kodu": "T01", "sube_adi": "Test Şubesi",
                "il": "Test", "ilce": "Merkez", "sube_tipi": "Merkez",
                "kabul_edilen": 100, "teslim_edilen": 90,
                "geciken": delayed, "iade_edilen": 5,
                "ortalama_teslim_suresi": 1.5 + (day % 3) * 0.05,
                "toplam_personel": 10, "dagitici_sayisi": 5,
                "sikayet_sayisi": 1, "toplam_gelir": 1000,
            })
        return pd.DataFrame(rows)

    def test_missing_columns_are_reported(self) -> None:
        with self.assertRaisesRegex(AnomalyDetectionError, "gerekli sütunlar eksik"):
            detect_anomalies(pd.DataFrame({"sube_kodu": ["A"]}))

    def test_empty_valid_frame_has_no_anomalies(self) -> None:
        empty = pd.DataFrame(columns=sorted(ANOMALY_SOURCE_COLUMNS))
        self.assertEqual(detect_anomalies(empty), [])

    def test_invalid_thresholds_are_rejected(self) -> None:
        data = pd.read_csv("data/sube_performans.csv", encoding="utf-8-sig")
        with self.assertRaisesRegex(AnomalyDetectionError, "eşikleri"):
            detect_anomalies(data, AnomalyConfig(4.0, 3.0, 30))

    def test_known_delay_spike_is_detected(self) -> None:
        anomalies = detect_anomalies(self._data_with_known_delay_anomaly())
        delay_anomalies = [
            item for item in anomalies if item.metric == "gecikme_orani_pct"
        ]
        self.assertEqual(len(delay_anomalies), 1)
        self.assertEqual(delay_anomalies[0].date, pd.Timestamp("2026-02-09"))
        self.assertEqual(delay_anomalies[0].severity, "yüksek")

    def test_sample_data_produces_explainable_anomalies(self) -> None:
        data = pd.read_csv("data/sube_performans.csv", encoding="utf-8-sig")
        anomalies = detect_anomalies(data)
        self.assertTrue(anomalies)
        self.assertTrue(all(item.anomaly_score >= 3.5 for item in anomalies))
        self.assertTrue(all(item.severity in {"orta", "yüksek"} for item in anomalies))
        self.assertTrue(all(item.suggested_check for item in anomalies))


if __name__ == "__main__":
    unittest.main()
