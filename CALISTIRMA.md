# Birleşik projeyi çalıştırma

## En kolay yöntem (Windows)

Proje kökündeki `BASLAT.bat` dosyasına çift tıklayın. Dosya Anaconda, uv ile
kurulmuş Python, normal Python ve `py` başlatıcısını sırayla kontrol eder;
bulduğu çalışan yorumlayıcıyla API ortamını kurar. Node.js/npm de ayrıca
kontrol edilir. İlk çalıştırma paketler indirileceği için birkaç dakika sürebilir.

İki terminal penceresi açık kalmalıdır:

- `PTT AI - FastAPI`: `Application startup complete.` yazmalıdır.
- `PTT AI - Next.js`: `Ready` yazmalıdır.

Ardından tarayıcıda `http://localhost:3000` adresini açın. Adresi terminale
yazmayın; Chrome/Edge adres çubuğuna yazın.

## VS Code'da açma

VS Code'da `Dosya > Klasör Aç` yolunu seçin ve ZIP'ten çıkardığınız
`PTT AI Projem` klasörünü açın. ZIP dosyasının kendisini açmayın. Terminali
VS Code içinde kullanacaksanız `Terminal > Yeni Terminal` seçeneğiyle iki
terminal açıp aşağıdaki komutları ayrı ayrı çalıştırın.

## Elle çalıştırma

### 1. FastAPI terminali

```powershell
python -m venv .api-venv
.\.api-venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.api-venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
```

### 2. Next.js terminali

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

- Web arayüzü: `http://localhost:3000`
- API belgeleri: `http://localhost:8000/docs`

Streamlit sürümü kaldırılmamıştır ve eski komutuyla ayrıca çalıştırılabilir.
