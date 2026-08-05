"""PTT şube performans projesi için tekrarlanabilir sentetik veri üretir."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path


SEED = 20260805
START_DATE = date(2026, 1, 1)
DAY_COUNT = 180

OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sube_performans.csv"
)

BRANCHES = [
    ("S001", "Ankara Çankaya", "Ankara", "Çankaya", "Merkez", 1.25, 24, 9),
    ("S002", "Ankara Keçiören", "Ankara", "Keçiören", "Büyük", 1.15, 21, 8),
    ("S003", "İstanbul Kadıköy", "İstanbul", "Kadıköy", "Merkez", 1.40, 28, 11),
    ("S004", "İstanbul Üsküdar", "İstanbul", "Üsküdar", "Büyük", 1.30, 25, 10),
    ("S005", "İzmir Konak", "İzmir", "Konak", "Merkez", 1.20, 23, 9),
    ("S006", "Bursa Nilüfer", "Bursa", "Nilüfer", "Büyük", 1.05, 19, 7),
    ("S007", "Antalya Muratpaşa", "Antalya", "Muratpaşa", "Büyük", 1.10, 20, 8),
    ("S008", "Konya Selçuklu", "Konya", "Selçuklu", "Orta", 0.90, 16, 6),
    ("S009", "Samsun İlkadım", "Samsun", "İlkadım", "Orta", 0.82, 15, 6),
    ("S010", "Erzurum Yakutiye", "Erzurum", "Yakutiye", "Orta", 0.75, 14, 5),
]

FIELDS = [
    "tarih",
    "sube_kodu",
    "sube_adi",
    "il",
    "ilce",
    "sube_tipi",
    "kabul_edilen",
    "teslim_edilen",
    "bekleyen",
    "geciken",
    "iade_edilen",
    "ortalama_teslim_suresi",
    "toplam_personel",
    "dagitici_sayisi",
    "gise_personeli",
    "izinli_personel",
    "fazla_mesai_saati",
    "sikayet_sayisi",
    "basarisiz_teslimat",
    "hasarli_gonderi",
    "yanlis_teslimat",
    "toplam_gelir",
    "kargo_geliri",
    "bankacilik_islem_sayisi",
    "tahsilat_sayisi",
    "hava_durumu",
    "resmi_tatil",
    "bayram_donemi",
    "bolgesel_yogunluk",
]


def clamp(value: float, lower: float, upper: float) -> float:
    """Bir değeri belirtilen alt ve üst sınırlar arasında tutar."""
    return max(lower, min(value, upper))


def weather_for(
    city: str,
    current: date,
    rng: random.Random,
) -> str:
    """Şehir ve mevsime göre örnek hava durumu üretir."""
    month = current.month
    roll = rng.random()

    if city == "Erzurum" and month in (1, 2, 3) and roll < 0.45:
        return "Karlı"

    if city in ("Samsun", "İstanbul", "Bursa") and roll < 0.25:
        return "Yağmurlu"

    if (
        month in (6, 7, 8)
        and city in ("Antalya", "İzmir")
        and roll < 0.45
    ):
        return "Sıcak"

    if roll < 0.15:
        return "Yağmurlu"

    if roll < 0.40:
        return "Bulutlu"

    return "Açık"


def make_row(
    branch: tuple,
    current: date,
    day_index: int,
    rng: random.Random,
) -> dict:
    """Bir şubenin bir günlük performans kaydını üretir."""
    (
        code,
        name,
        city,
        district,
        branch_type,
        scale,
        personnel,
        couriers,
    ) = branch

    weekend = current.weekday() >= 5

    official_holiday = current in {
        date(2026, 1, 1),
        date(2026, 4, 23),
        date(2026, 5, 1),
        date(2026, 5, 19),
    }

    holiday_period = (
        date(2026, 3, 19) <= current <= date(2026, 3, 22)
        or date(2026, 5, 26) <= current <= date(2026, 5, 30)
    )

    weather = weather_for(city, current, rng)

    seasonal = 1 + 0.10 * math.sin(day_index / 18)

    if current.weekday() == 0:
        weekday_factor = 1.18
    elif weekend:
        weekday_factor = 0.48
    else:
        weekday_factor = 1.0

    if holiday_period:
        holiday_factor = 1.30
    elif official_holiday:
        holiday_factor = 0.35
    else:
        holiday_factor = 1.0

    density = clamp(
        scale * seasonal * holiday_factor + rng.gauss(0, 0.08),
        0.55,
        1.85,
    )

    accepted = max(
        25,
        round(
            340 * density * weekday_factor
            + rng.gauss(0, 22)
        ),
    )

    leave = max(
        0,
        min(
            personnel // 3,
            round(rng.gauss(1.5, 1.1)),
        ),
    )

    # Çankaya şubesinde son 60 günde kontrollü bir
    # performans bozulması oluşturulur.
    if code == "S001":
        degradation = (
            0.07 * max(0, day_index - 120) / 59
        )
    else:
        degradation = 0

    weather_penalties = {
        "Açık": 0,
        "Bulutlu": 0.005,
        "Yağmurlu": 0.035,
        "Karlı": 0.085,
        "Sıcak": 0.018,
    }

    weather_penalty = weather_penalties[weather]

    active_couriers = max(
        1,
        couriers - min(leave, couriers - 1),
    )

    workload = accepted / active_couriers

    workload_penalty = (
        max(0, workload - 48) * 0.0018
    )

    success_rate = clamp(
        0.965
        - weather_penalty
        - workload_penalty
        - degradation
        + rng.gauss(0, 0.009),
        0.72,
        0.99,
    )

    returned = max(
        0,
        round(
            accepted
            * clamp(
                0.018 + rng.gauss(0, 0.005),
                0.006,
                0.05,
            )
        ),
    )

    delivered = max(
        0,
        round(accepted * success_rate) - returned,
    )

    delayed = max(
        0,
        round(
            accepted
            * clamp(
                1
                - success_rate
                + rng.gauss(0.01, 0.006),
                0.01,
                0.24,
            )
        ),
    )

    pending = max(
        0,
        accepted - delivered - returned,
    )

    failed = max(
        returned,
        round(
            accepted
            * clamp(
                0.025
                + weather_penalty
                + degradation / 2
                + rng.gauss(0, 0.006),
                0.008,
                0.14,
            )
        ),
    )

    avg_delivery = clamp(
        1.35
        + weather_penalty * 10
        + workload_penalty * 7
        + degradation * 8
        + rng.gauss(0, 0.12),
        0.8,
        4.5,
    )

    complaints = max(
        0,
        round(
            (delayed + failed) * 0.10
            + rng.gauss(0, 1.2)
        ),
    )

    damaged = max(
        0,
        round(
            accepted
            * clamp(
                rng.gauss(0.004, 0.0015),
                0.001,
                0.012,
            )
        ),
    )

    wrong = max(
        0,
        round(
            accepted
            * clamp(
                rng.gauss(0.0025, 0.001),
                0,
                0.009,
            )
        ),
    )

    overtime = max(
        0,
        (workload - 42) * couriers * 0.08
        + rng.gauss(1.5, 1.2),
    )

    cargo_revenue = (
        delivered * rng.uniform(36, 48)
    )

    banking = max(
        5,
        round(
            accepted * rng.uniform(0.32, 0.55)
        ),
    )

    collections = max(
        2,
        round(
            banking * rng.uniform(0.30, 0.55)
        ),
    )

    total_revenue = (
        cargo_revenue
        + banking * rng.uniform(14, 22)
        + collections * rng.uniform(8, 14)
    )

    return {
        "tarih": current.isoformat(),
        "sube_kodu": code,
        "sube_adi": name,
        "il": city,
        "ilce": district,
        "sube_tipi": branch_type,
        "kabul_edilen": accepted,
        "teslim_edilen": delivered,
        "bekleyen": pending,
        "geciken": delayed,
        "iade_edilen": returned,
        "ortalama_teslim_suresi": round(
            avg_delivery,
            2,
        ),
        "toplam_personel": personnel,
        "dagitici_sayisi": couriers,
        "gise_personeli": max(
            2,
            personnel - couriers - 5,
        ),
        "izinli_personel": leave,
        "fazla_mesai_saati": round(
            overtime,
            1,
        ),
        "sikayet_sayisi": complaints,
        "basarisiz_teslimat": failed,
        "hasarli_gonderi": damaged,
        "yanlis_teslimat": wrong,
        "toplam_gelir": round(
            total_revenue,
            2,
        ),
        "kargo_geliri": round(
            cargo_revenue,
            2,
        ),
        "bankacilik_islem_sayisi": banking,
        "tahsilat_sayisi": collections,
        "hava_durumu": weather,
        "resmi_tatil": int(official_holiday),
        "bayram_donemi": int(holiday_period),
        "bolgesel_yogunluk": round(
            density,
            2,
        ),
    }


def main() -> None:
    """Bütün şubeler için CSV veri setini oluşturur."""
    rng = random.Random(SEED)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = [
        make_row(
            branch,
            START_DATE + timedelta(days=day_index),
            day_index,
            rng,
        )
        for day_index in range(DAY_COUNT)
        for branch in BRANCHES
    ]

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDS,
        )
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"{len(rows)} satır oluşturuldu: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()