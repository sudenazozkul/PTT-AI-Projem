# Entegrasyon özeti

## Yaklaşım

- `src/ptt_ai_projem/`, `scripts/`, `data/`, `pages/` ve `app.py` içindeki
  mevcut dosyalar değiştirilmedi.
- `backend/` yalnızca adaptör katmanıdır. Mevcut `load_branch_data`,
  `validate_branch_data`, `calculate_daily_kpis`, `calculate_branch_summary`,
  `analyze_branches`, `create_recommendations` ve `detect_anomalies`
  fonksiyonlarını import ederek sonuçları JSON biçimine dönüştürür.
- `frontend/`, onaylanan sarı üst şeritli ve yatay navigasyonlu tasarımın
  Next.js karşılığıdır. Hesaplama yapmaz; FastAPI endpoint'lerinden veri alır.
- Sekiz KPI ve ağırlıklı ortalama teslim süresi, orijinal Python formüllerinden
  üretilir; arayüzde yöntem kartlarıyla görünür durumdadır.
- Şube karşılaştırmasında seçilen 2–6 şubeye birbirinden farklı, sabit renkler
  atanır. Uydurma birleşik puan veya normalize radar skoru kullanılmaz.
- Yapay Zekâ Danışmanı ekranı özellikle boş bırakılmıştır. İleride bağlanacak
  LLM için yalnızca pasif bir yer tutucu vardır; sahte yanıt üretmez.
- Üst başlıkta projenin özgün `PTT_bayragi.png` görseli kullanılır.

## Eklenen klasörler

- `backend/`: FastAPI uygulaması, adaptör servisi ve entegrasyon testleri
- `frontend/`: Next.js App Router arayüzü, ortak bileşenler ve beş sayfa

## Korunan özgün dosyalar

`src/ptt_ai_projem/`, `scripts/`, `data/`, `pages/`, `tests/` ve `app.py`
değiştirilmemiştir. Next.js/FastAPI entegrasyonu bu kodları adaptör olarak
kullanır; eski Streamlit sürümü ayrıca çalıştırılabilir.
