"""Analiz bulgularını temkinli ve uygulanabilir önerilere dönüştürür."""

from __future__ import annotations

from dataclasses import dataclass

from ptt_ai_projem.analysis import Finding


@dataclass(frozen=True)
class Recommendation:
    finding: Finding
    action: str


RULE_ACTIONS = {
    "high_delay": "Geciken gönderiler rota, gün ve yoğunluk kırılımında incelenebilir; en yoğun dilimler için kapasite planı güncellenebilir.",
    "high_workload": "Yoğun günlerde geçici dağıtıcı desteği, vardiya dengeleme veya rota optimizasyonu değerlendirilebilir.",
    "leave_delay_relation": "İzin planı yoğunluk tahminleriyle birlikte gözden geçirilebilir ve kritik günler için yedek kapasite planlanabilir.",
    "delivery_time_increase": "Son 30 gündeki rota, iş yükü ve personel değişimleri karşılaştırılarak artışın kaynağı araştırılabilir.",
    "complaint_trend": "Son şikâyetler konu ve rota bazında sınıflandırılıp tekrarlayan sorunlar için sorumlu ve termin belirlenebilir.",
    "weather_delay_relation": "Olumsuz hava beklenen günlerde rota süreleri ve müşteri bilgilendirme planı önceden güncellenebilir.",
    "overtime_success_relation": "Fazla mesainin yoğunlaştığı vardiyalarda iş dağılımı ve dinlenme süreleri gözden geçirilebilir.",
}


def create_recommendations(findings: list[Finding]) -> list[Recommendation]:
    """Bilinen her bulgu kuralı için standart bir operasyonel aksiyon üretir."""
    return [
        Recommendation(finding=finding, action=RULE_ACTIONS[finding.rule_id])
        for finding in findings
        if finding.rule_id in RULE_ACTIONS
    ]
