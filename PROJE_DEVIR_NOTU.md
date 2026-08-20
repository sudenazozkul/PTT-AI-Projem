# PTT AI Şube Performans Danışmanı — Proje Devir Notu

Bu belge, projeye yeni bir Codex/ChatGPT sohbetinde kaldığı yerden devam edebilmek için hazırlanmıştır. Bilgiler 13 Ağustos 2026 tarihindeki çalışma klasörünün güncel durumunu esas alır.

## Yeni sohbette kullanılacak mesaj

> `PROJE_DEVIR_NOTU.md` dosyasını ve mevcut proje dosyalarını incele. Belgede belirtilen güncel durumu esas alarak projeye kaldığımız yerden devam et. Mevcut çalışan özellikleri bozma, önce Git durumunu kontrol et ve sıradaki ana adım olan kural tabanlı analiz/öneri modülünden devam et.

## Projenin amacı

PTT şubelerinin operasyonel performans verilerini analiz eden, KPI'ları hesaplayan, şubeleri karşılaştıran ve daha sonra yapay zekâ destekli açıklama ve öneri sunacak bir karar destek sistemi geliştiriliyor.

Sistem şu sorulara cevap vermeyi hedefliyor:

- Hangi şubelerin performansı düşüyor?
- Teslim süresi veya gecikme neden artmış olabilir?
- Şubeler benzer ölçekte nasıl karşılaştırılır?
- Personel ve dağıtıcı iş yükü performansı nasıl etkiliyor?
- Hangi operasyonel aksiyonlar önerilebilir?
- Yönetici doğal dille soru sorduğunda veriye dayalı cevap üretilebilir mi?

## Teknolojiler

- Python 3.12
- Pandas 3.x
- Streamlit 1.61.1
- Plotly 6.9.0
- `uv` paket ve sanal ortam yönetimi
- Git ve GitHub

Proje yolu:

```text
C:\Users\ASUS\OneDrive\Masaüstü\PTT AI Projem
```

## Güncel dosya yapısı

```text
PTT AI Projem/
├── app.py
├── PTT_bayragi.png
├── pyproject.toml
├── uv.lock
├── .gitignore
├── data/
│   ├── sube_performans.csv
│   ├── gunluk_kpi.csv
│   └── sube_kpi_ozet.csv
├── pages/
│   ├── 0_Genel_Bakis.py
│   ├── 1_Sube_Detayi.py
│   └── 2_Sube_Karsilastirma.py
├── scripts/
│   ├── generate_sample_data.py
│   ├── validate_data.py
│   └── calculate_kpis.py
└── src/ptt_ai_projem/
    ├── __init__.py
    ├── data_loader.py
    ├── validation.py
    ├── kpi.py
    └── test.py
```

## Kurulum ve çalıştırma

Sanal ortamı etkinleştirme:

```powershell
.\.venv\Scripts\Activate.ps1
```

Bağımlılıkları eşitleme:

```powershell
uv sync
```

OneDrive erişim kilidi nedeniyle sorun çıkarsa:

```powershell
uv pip install --python .\.venv\Scripts\python.exe streamlit plotly
```

Uygulamayı başlatma:

```powershell
python -m streamlit run app.py
```

Yerel adres:

```text
http://localhost:8501
```

Sunucuyu durdurmak için `Ctrl+C` kullanılır.

## 1. aşama — Sentetik veri üretimi

Dosya:

```text
scripts/generate_sample_data.py
```

Çıktı:

```text
data/sube_performans.csv
```

Veri seti:

- 10 şube
- 180 gün
- 1 Ocak–29 Haziran 2026
- 1.800 günlük kayıt
- 29 sütun
- Her satır bir şubenin bir gününü temsil ediyor
- `SEED = 20260805` ile tekrar üretilebilir

Seed günlük değerleri birbirine eşitlemez. Program yeniden çalıştırıldığında aynı sentetik veri dizisinin tekrar oluşmasını sağlar.

Veride bilinçli ilişkiler bulunuyor:

- Pazartesi günleri işlem hacmi daha yüksek
- Hafta sonu hacmi daha düşük
- Yağmur ve kar teslim süresini/gecikmeyi etkiliyor
- İzinli personel aktif dağıtıcı sayısını azaltıyor
- Dağıtıcı iş yükü yükselince başarı düşebiliyor
- Fazla mesai iş yüküyle ilişkili
- Şikâyetler gecikme ve başarısız teslimatla ilişkili
- Ankara Çankaya'da son 60 güne doğru kontrollü performans bozulması var

Yeniden üretme:

```powershell
python scripts\generate_sample_data.py
```

Beklenen çıktı:

```text
1800 satır oluşturuldu: ...\data\sube_performans.csv
```

## Ham veri alanları

Şube bilgileri:

```text
tarih, sube_kodu, sube_adi, il, ilce, sube_tipi
```

Operasyon:

```text
kabul_edilen, teslim_edilen, bekleyen, geciken, iade_edilen,
ortalama_teslim_suresi
```

Personel:

```text
toplam_personel, dagitici_sayisi, gise_personeli,
izinli_personel, fazla_mesai_saati
```

Kalite:

```text
sikayet_sayisi, basarisiz_teslimat, hasarli_gonderi,
yanlis_teslimat
```

Finans ve çevre:

```text
toplam_gelir, kargo_geliri, bankacilik_islem_sayisi,
tahsilat_sayisi, hava_durumu, resmi_tatil, bayram_donemi,
bolgesel_yogunluk
```

## 2. aşama — Veri okuma ve doğrulama

### `data_loader.py`

- Dosya mevcut mu?
- Yol gerçekten dosya mı?
- Uzantı CSV mi?
- CSV boş veya bozuk mu?
- UTF-8/Excel uyumlu okunabiliyor mu?
- Sütun ve metin çevresindeki boşlukların temizlenmesi
- Sadece boşluk içeren hücrelerin `pd.NA` yapılması
- Hataların anlaşılır `DataLoadError` mesajlarına çevrilmesi

### `validation.py`

- 29 zorunlu sütun mevcut mu?
- Boş hücre var mı?
- Tarihler `YYYY-MM-DD` biçiminde mi?
- Sayısal alanlarda metin var mı?
- Negatif değer var mı?
- Aynı tarih ve şube tekrarlanmış mı?
- `kabul_edilen = teslim_edilen + bekleyen + iade_edilen` eşitliği sağlanıyor mu?
- Dağıtıcı/izinli personel toplam personelden fazla mı?
- Tatil alanları yalnızca `0/1` mi?
- Hava durumu tanımlı kategorilerden biri mi?

Doğrulama komutu:

```powershell
python scripts\validate_data.py
```

Beklenen çıktı:

```text
Kontrol edilen kayıt sayısı: 1800
Kontrol edilen sütun sayısı: 29
[BASARILI] Veri seti kullanıma hazır.
```

## 3. aşama — KPI hesaplama

Ana modül:

```text
src/ptt_ai_projem/kpi.py
```

Formüller:

```text
teslim_basarisi_pct = teslim_edilen / kabul_edilen × 100
gecikme_orani_pct = geciken / kabul_edilen × 100
iade_orani_pct = iade_edilen / kabul_edilen × 100
sikayet_orani_binde = sikayet_sayisi / teslim_edilen × 1000
personel_verimliligi = teslim_edilen / toplam_personel
dagitici_is_yuku = kabul_edilen / dagitici_sayisi
gonderi_basi_gelir = toplam_gelir / kabul_edilen
```

`_safe_divide()` sıfıra bölme hatasını engeller.

Şube özetlerinde günlük yüzdelerin basit ortalaması alınmaz. Toplam teslim/toplam kabul gibi ağırlıklı yöntemler kullanılır. Ortalama teslim süresi teslimat sayısına göre ağırlıklandırılır. Personel ve dağıtıcı hesaplarında personel-gün/dağıtıcı-gün yaklaşımı kullanılır.

KPI çıktıları:

```powershell
python scripts\calculate_kpis.py
```

```text
data/gunluk_kpi.csv
data/sube_kpi_ozet.csv
```

Dosya farkları:

- `sube_performans.csv`: Ham kaynak, 29 sütun
- `gunluk_kpi.csv`: Ham veri + 7 KPI, 1.800 satır
- `sube_kpi_ozet.csv`: Her şube için tek özet satırı, 10 satır

Dashboard çıktı CSV'lerini doğrudan okumaz. Ham `sube_performans.csv` dosyasını okuyup doğrular ve KPI'ları bellekte yeniden hesaplar.

## 4. aşama — Streamlit dashboard

### Navigasyon (`app.py`)

`app.py` yalnızca `st.navigation()` ile Türkçe sayfa menüsünü yönetiyor:

```text
Genel Bakış
Şube Detayı
Şube Karşılaştırma
```

- Teknik `app` adı kullanıcıya gösterilmiyor
- Menü ve başlıklardaki emoji/simgeler kaldırıldı
- Sayfa isimleri tamamen Türkçe
- PTT logosu sidebar'ın üstünde tam genişlikte arka plan olarak gösteriliyor
- Logo base64'e çevrilip sidebar header CSS'ine bağlanıyor
- Logo alanı yaklaşık 156 px yüksekliğinde ve `background-size: cover` kullanıyor

### Genel Bakış (`pages/0_Genel_Bakis.py`)

- PTT sarı/lacivert teması
- Tarih aralığı filtresi
- İl filtresi
- Şube tipi filtresi
- Şube filtresi
- Toplam gönderi kartı
- Ağırlıklı teslim başarısı kartı
- Ağırlıklı ortalama teslim süresi kartı
- Toplam şikâyet kartı
- Toplam gelir kartı
- En başarılı şube: teslim başarısı en yüksek şube
- En riskli şube: gecikme oranı en yüksek şube
- Şube teslim başarısı karşılaştırma grafiği
- Aylık teslim başarısı trendi
- Aylık gecikme oranı
- Her 1.000 teslimattaki şikâyet grafiği
- Şube performans sıralama tablosu

Filtreler kartları, özetleri, grafikleri ve tabloyu yeniden hesaplar.

### Şube Detayı (`pages/1_Sube_Detayi.py`)

- Tek şube seçimi
- Tarih aralığı
- Teslim başarısı
- Gecikme oranı
- Ortalama teslim süresi
- Personel verimliliği
- Dağıtıcı iş yükü
- Son 30 gün ile önceki 30 gün arasındaki değişimler
- Aylık başarı ve gecikme eğilimi
- İş yükü ve personel verimliliği grafiği
- Ortalama teslim süresi grafiği
- Aylık gönderi hacmi
- Günlük KPI tablosu

### Şube Karşılaştırma (`pages/2_Sube_Karsilastirma.py`)

- En az 2, en fazla 6 şube seçimi
- Tarih aralığı
- En yüksek teslim başarısı
- En düşük gecikme
- En yüksek personel verimliliği
- En yüksek gönderi başına gelir
- Seçilebilir KPI karşılaştırma grafiği
- Aylık teslim başarısı karşılaştırması
- Aylık gecikme karşılaştırması
- Ayrıntılı KPI karşılaştırma tablosu

## Önemli ürün kararları

### Performans puanı kaldırıldı

Bir ara KPI ağırlıklarıyla `0–100` performans puanı oluşturuldu. Ancak ağırlıklar ve hedefler gerçek PTT kurumsal hedeflerinden gelmediği için kaldırıldı.

Silinen dosyalar:

```text
src/ptt_ai_projem/scoring.py
scripts/calculate_scores.py
data/sube_performans_puanlari.csv
```

Dashboard açıklanabilir gerçek KPI'ları doğrudan gösteriyor. Gerçek kurumsal hedefler sağlanırsa puanlama yeniden değerlendirilebilir.

### Yapay zekâ henüz eklenmedi

Henüz LLM/Ollama entegrasyonu yapılmadı. Önce Python tarafında güvenilir analiz bulguları ve kurallar oluşturulacak. LLM daha sonra sayısal bulguları Türkçeye çevirecek; hesaplama yapması veya veri uydurması istenmeyecek.

## Güncel Git durumu

Bu belge hazırlanırken şu değişiklikler henüz commit edilmemişti:

```text
M app.py
M pages/1_Sube_Detayi.py
M pages/2_Sube_Karsilastirma.py
?? pages/0_Genel_Bakis.py
?? PROJE_DEVIR_NOTU.md
```

Yeni sohbette ilk işlem:

```powershell
git status
```

Kullanıcı onaylarsa:

```powershell
git add app.py pages/0_Genel_Bakis.py pages/1_Sube_Detayi.py pages/2_Sube_Karsilastirma.py PROJE_DEVIR_NOTU.md
git commit -m "Türkçe navigasyonu ve proje devir notunu ekle"
git push
```

## Git dışında tutulan kişisel notlar

`.gitignore` içinde:

```gitignore
Proje Hakkında Bilgiler*.txt
Dashboard Hakkında Bilgiler*.txt
```

Bu notlar bilgisayarda kalır, GitHub'a gönderilmez. `.venv`, `__pycache__` ve derleme çıktıları da Git'e eklenmemelidir.

## Test komutları

Sözdizimi:

```powershell
python -m py_compile app.py pages\0_Genel_Bakis.py pages\1_Sube_Detayi.py pages\2_Sube_Karsilastirma.py
```

Veri doğrulama:

```powershell
python scripts\validate_data.py
```

KPI çıktıları:

```powershell
python scripts\calculate_kpis.py
```

Manuel arayüz testi:

```powershell
python -m streamlit run app.py
```

Kontrol listesi:

- Sidebar logosu üst alanı tam genişlikte kaplıyor mu?
- Menü adları Türkçe mi?
- Genel Bakış filtreleri kart ve grafikleri değiştiriyor mu?
- Ankara seçilince iki şube kalıyor mu?
- Şube Detayı seçime göre güncelleniyor mu?
- Karşılaştırmada en az iki şube kontrolü çalışıyor mu?
- Türkçe karakterler düzgün mü?

## 5. aşama — Kural tabanlı analiz ve öneriler

Ana modüller:

```text
src/ptt_ai_projem/analysis.py
src/ptt_ai_projem/recommendations.py
scripts/run_analysis.py
```

Yedi açıklanabilir kural şube bazında gecikme, iş yükü, personel izni,
teslim süresi eğilimi, şikâyet eğilimi, hava koşulları ve fazla mesai
ilişkilerini inceler. Kurum karşılaştırmalarında ağırlıklı KPI'lar kullanılır.
İlişkisel bulgular kesin neden olarak sunulmaz. Eşikler `AnalysisConfig` ile
değiştirilebilir ve her bulgu hesaplanan kanıt değerlerini taşır.

Analiz raporu:

```powershell
python scripts\run_analysis.py
```

Testler:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Analiz ve Öneriler dashboard'u

`pages/3_Analiz_ve_Oneriler.py` sayfası navigasyona eklendi. Sayfa tarih,
şube ve önem seviyesi filtreleri; özet kartları; açıklanabilir bulgu kartları;
sayısal kanıtlar; operasyonel öneriler; toplu tablo ve CSV indirme sunar.
Kurum karşılaştırması tarih aralığındaki bütün şubeler üzerinden hesaplanır;
şube filtresi yalnızca gösterilen sonuçları sınırlar.

## Sıradaki ana adım

```text
AI açıklama panelinin tasarlanması
```

## Risk ve anomali analizi

`src/ptt_ai_projem/anomaly.py`, şubelerin günlük gecikme, teslim süresi,
şikâyet, dağıtıcı iş yükü ve teslim başarısı KPI'larını şubenin kendi olağan
dağılımıyla karşılaştırır. Uç değerlerden daha az etkilenen medyan ve MAD
yöntemi kullanılır. Her sinyal tarih, gerçekleşen değer, olağan medyan,
göreli sapma, anomali skoru, önem seviyesi ve önerilen incelemeyi taşır.
Keyfî bir birleşik performans/risk puanı üretilmez.

Terminal raporu:

```powershell
python scripts\run_anomaly_analysis.py
```

Uygulanan analiz kuralları:

- Gecikme oranı kurum ortalamasının belirgin üzerinde mi?
- Dağıtıcı başına iş yükü kurum ortalamasının üzerinde mi?
- İzinli personel yükseldiğinde gecikme de yükselmiş mi?
- Teslim süresi son 30 günde önceki 30 güne göre artmış mı?
- Şikâyet oranı son haftalarda düzenli yükseliyor mu?
- Kötü hava ile gecikme aynı dönemde artmış mı?
- Fazla mesai artarken teslim başarısı düşmüş mü?

Örnek çıktı:

```text
Bulgu: Çankaya şubesinde teslim süresi son 30 günde önceki döneme göre arttı.
Olası neden: Dağıtıcı başına iş yükü aynı dönemde kurum ortalamasının üzerine çıktı.
Öneri: Yoğun günlerde ek dağıtıcı görevlendirme veya rota optimizasyonu değerlendirilebilir.
```

Kesin nedensellik iddia edilmemeli. Veri yalnızca ilişki gösteriyorsa “olası neden”, “ilişkili olabilir” veya “incelenmelidir” denmeli.

## Daha sonraki sıra

1. Kural tabanlı analiz
2. Otomatik operasyonel öneriler
3. Anomali/risk analizi
4. AI analiz paneli
5. Ollama + yerel LLM entegrasyonu
6. Doğal dil soru-cevap ekranı
7. Testler ve kullanıcı dokümantasyonu

LLM'e ham veri yerine Python tarafından hesaplanmış bulgu ve özetler verilmelidir.

## Tamamlanma özeti

```text
[Tamamlandı] Sentetik veri üretimi
[Tamamlandı] Veri okuma
[Tamamlandı] Veri doğrulama
[Tamamlandı] Günlük KPI hesaplama
[Tamamlandı] Şube KPI özeti
[Tamamlandı] Genel Bakış dashboard'u
[Tamamlandı] Şube Detayı ekranı
[Tamamlandı] Şube Karşılaştırma ekranı
[Tamamlandı] Türkçe özel navigasyon
[Tamamlandı] Kural tabanlı analiz
[Tamamlandı] Operasyonel öneriler
[Tamamlandı] Analiz ve önerilerin dashboard'a eklenmesi
[Tamamlandı] Risk/anomali analizi
[Tamamlandı] Risk/anomali bulgularının dashboard'a eklenmesi
[Bekliyor] AI açıklama paneli
[Bekliyor] AI açıklama modülü
[Bekliyor] AI sohbet ekranı
```
