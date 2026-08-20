# PTT AI web arayüzü

Next.js App Router, TypeScript, Tailwind CSS, Motion ve Recharts ile oluşturulan
arayüzdür. Bütün verileri yeni FastAPI adaptöründen alır; Python tarafındaki
hesaplama formüllerini tarayıcıda tekrar etmez.

Arayüzde Genel Bakış, Şube Detayı, 2–6 Şube Karşılaştırması, Analiz &
Anomaliler ve gelecekteki LLM için boş AI Danışman sayfası bulunur. KPI
formülleri yöntem endpoint'inden okunup matematiksel ifadeleriyle gösterilir.

## Çalıştırma

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Arayüz: `http://localhost:3000`
