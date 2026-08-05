"""CSV veri dosyalarını güvenli şekilde okuma işlemleri."""

from pathlib import Path

import pandas as pd


class DataLoadError(Exception):
    """Veri dosyası okunamadığında oluşan anlaşılır uygulama hatası."""


def load_branch_data(file_path: str | Path) -> pd.DataFrame:
    """Şube performans CSV dosyasını okuyup DataFrame olarak döndürür."""
    path = Path(file_path)

    if not path.exists():
        raise DataLoadError(f"Veri dosyası bulunamadı: {path}")

    if not path.is_file():
        raise DataLoadError(f"Verilen yol bir dosya değil: {path}")

    if path.suffix.lower() != ".csv":
        raise DataLoadError("Yalnızca .csv uzantılı dosyalar destekleniyor.")

    try:
        data = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataLoadError("CSV dosyası UTF-8 biçiminde okunamadı.") from exc
    except pd.errors.EmptyDataError as exc:
        raise DataLoadError("CSV dosyası tamamen boş.") from exc
    except pd.errors.ParserError as exc:
        raise DataLoadError("CSV satır ve sütun yapısı bozuk.") from exc

    # Başlıklardaki yanlışlıkla bırakılmış boşlukları temizler.
    data.columns = data.columns.str.strip()

    # Sadece boşluk içeren hücreleri gerçek eksik değer hâline getirir.
    text_columns = data.select_dtypes(include="object").columns
    for column in text_columns:
        data[column] = data[column].apply(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        data[column] = data[column].replace("", pd.NA)

    return data
