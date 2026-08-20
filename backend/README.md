# FastAPI entegrasyon katmanı

Bu klasör, `src/ptt_ai_projem/` altındaki mevcut iş mantığını değiştirmeden HTTP
endpoint'leri üzerinden sunar. Veri yükleme, doğrulama, KPI, analiz, öneri ve
anomali sonuçları doğrudan orijinal fonksiyonlardan alınır.

Sunulan uçlar: `/api/meta`, `/api/methodology`, `/api/branches`,
`/api/overview`, `/api/branches/{kod}`, `/api/comparison` ve `/api/analysis`.
Yapay zekâ ucu bilinçli olarak eklenmemiştir; daha sonra kurulacak LLM
entegrasyonu için boş bırakılmıştır.

## Çalıştırma

```powershell
python -m venv .api-venv
.\.api-venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

API belgeleri: `http://localhost:8000/docs`
