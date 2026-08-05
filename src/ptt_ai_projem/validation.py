"""PTT şube performans verisi için doğrulama kuralları."""

from dataclasses import dataclass, field

import pandas as pd


REQUIRED_COLUMNS = [
    "tarih", "sube_kodu", "sube_adi", "il", "ilce", "sube_tipi",
    "kabul_edilen", "teslim_edilen", "bekleyen", "geciken", "iade_edilen",
    "ortalama_teslim_suresi", "toplam_personel", "dagitici_sayisi",
    "gise_personeli", "izinli_personel", "fazla_mesai_saati", "sikayet_sayisi",
    "basarisiz_teslimat", "hasarli_gonderi", "yanlis_teslimat", "toplam_gelir",
    "kargo_geliri", "bankacilik_islem_sayisi", "tahsilat_sayisi",
    "hava_durumu", "resmi_tatil", "bayram_donemi", "bolgesel_yogunluk",
]

NUMERIC_COLUMNS = [
    "kabul_edilen", "teslim_edilen", "bekleyen", "geciken", "iade_edilen",
    "ortalama_teslim_suresi", "toplam_personel", "dagitici_sayisi",
    "gise_personeli", "izinli_personel", "fazla_mesai_saati", "sikayet_sayisi",
    "basarisiz_teslimat", "hasarli_gonderi", "yanlis_teslimat", "toplam_gelir",
    "kargo_geliri", "bankacilik_islem_sayisi", "tahsilat_sayisi",
    "resmi_tatil", "bayram_donemi", "bolgesel_yogunluk",
]

ALLOWED_WEATHER = {"Açık", "Bulutlu", "Yağmurlu", "Karlı", "Sıcak"}


@dataclass
class ValidationResult:
    """Doğrulama sonunda oluşan hata, uyarı ve temizlenmiş veriler."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cleaned_data: pd.DataFrame | None = None

    @property
    def is_valid(self) -> bool:
        """Hiç hata yoksa verinin kullanılabilir olduğunu bildirir."""
        return not self.errors


def _row_numbers(mask: pd.Series, limit: int = 5) -> str:
    """Hatalı DataFrame indekslerini CSV satır numarasına dönüştürür."""
    rows = (mask[mask].index + 2).tolist()
    shown = ", ".join(str(row) for row in rows[:limit])
    return shown + ("..." if len(rows) > limit else "")


def validate_branch_data(data: pd.DataFrame) -> ValidationResult:
    """Şube verisini kurallara göre kontrol eder ve sonucu döndürür."""
    result = ValidationResult()

    if data.empty:
        result.errors.append("Veri dosyasında hiç kayıt bulunmuyor.")
        return result

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        result.errors.append(
            "Zorunlu sütunlar eksik: " + ", ".join(missing_columns)
        )
        return result

    cleaned = data.copy()

    # Zorunlu alanlardaki boş hücreleri kontrol eder.
    missing_cells = cleaned[REQUIRED_COLUMNS].isna().sum()
    for column, count in missing_cells[missing_cells > 0].items():
        result.errors.append(f"'{column}' sütununda {count} boş değer var.")

    # Tarihler geçerli mi kontrol eder; doğru tarihleri datetime tipine çevirir.
    parsed_dates = pd.to_datetime(cleaned["tarih"], format="%Y-%m-%d", errors="coerce")
    invalid_dates = parsed_dates.isna() & cleaned["tarih"].notna()
    if invalid_dates.any():
        result.errors.append(
            "Geçersiz tarih bulunan CSV satırları: " + _row_numbers(invalid_dates)
        )
    cleaned["tarih"] = parsed_dates

    # Sayısal olması gereken alanlarda metin bulunup bulunmadığını kontrol eder.
    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(cleaned[column], errors="coerce")
        invalid_numbers = converted.isna() & cleaned[column].notna()
        if invalid_numbers.any():
            result.errors.append(
                f"'{column}' sütununda sayısal olmayan değer bulunan CSV satırları: "
                + _row_numbers(invalid_numbers)
            )
        cleaned[column] = converted

    # Sayı alanlarında negatif değer olmamalıdır.
    for column in NUMERIC_COLUMNS:
        negative = cleaned[column] < 0
        if negative.any():
            result.errors.append(
                f"'{column}' sütununda negatif değer bulunan CSV satırları: "
                + _row_numbers(negative)
            )

    # Aynı şube ve tarih için yalnızca bir kayıt bulunmalıdır.
    duplicates = cleaned.duplicated(subset=["tarih", "sube_kodu"], keep=False)
    if duplicates.any():
        result.errors.append(
            "Aynı tarih ve şube koduna sahip tekrarlı CSV satırları: "
            + _row_numbers(duplicates)
        )

    # Kabul edilen gönderiler teslim, bekleyen ve iadelerin toplamı olmalıdır.
    operation_total = (
        cleaned["teslim_edilen"]
        + cleaned["bekleyen"]
        + cleaned["iade_edilen"]
    )
    inconsistent = cleaned["kabul_edilen"] != operation_total
    if inconsistent.any():
        result.errors.append(
            "kabul_edilen = teslim_edilen + bekleyen + iade_edilen eşitliğini "
            "sağlamayan CSV satırları: " + _row_numbers(inconsistent)
        )

    # İş kurallarına aykırı personel değerlerini kontrol eder.
    invalid_couriers = cleaned["dagitici_sayisi"] > cleaned["toplam_personel"]
    if invalid_couriers.any():
        result.errors.append(
            "Dağıtıcı sayısı toplam personelden büyük olan CSV satırları: "
            + _row_numbers(invalid_couriers)
        )

    invalid_leave = cleaned["izinli_personel"] > cleaned["toplam_personel"]
    if invalid_leave.any():
        result.errors.append(
            "İzinli personel sayısı toplam personelden büyük olan CSV satırları: "
            + _row_numbers(invalid_leave)
        )

    invalid_binary = ~cleaned["resmi_tatil"].isin([0, 1]) | ~cleaned[
        "bayram_donemi"
    ].isin([0, 1])
    if invalid_binary.any():
        result.errors.append(
            "Tatil alanları yalnızca 0 veya 1 olmalıdır. Hatalı CSV satırları: "
            + _row_numbers(invalid_binary)
        )

    unknown_weather = ~cleaned["hava_durumu"].isin(ALLOWED_WEATHER)
    if unknown_weather.any():
        result.warnings.append(
            "Tanımlanmamış hava durumu bulunan CSV satırları: "
            + _row_numbers(unknown_weather)
        )

    result.cleaned_data = cleaned
    return result
