"""PTT AI Şube Performans Danışmanı FastAPI giriş noktası."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.service import (
    IntegrationDataError,
    get_analysis,
    get_branch_detail,
    get_branches,
    get_comparison,
    get_metadata,
    get_methodology,
    get_overview,
)


app = FastAPI(
    title="PTT AI Şube Performans Danışmanı API",
    version="2.0.0",
    description="Mevcut doğrulama, KPI, analiz ve anomali modülleri için adaptör API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrationDataError)
async def integration_error_handler(_, error: IntegrationDataError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=422, content={"detail": str(error)})


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta")
def metadata():
    return get_metadata()


@app.get("/api/methodology")
def methodology():
    return get_methodology()


@app.get("/api/branches")
def branches():
    return get_branches()


@app.get("/api/overview")
def overview(
    start_date: str | None = None,
    end_date: str | None = None,
    provinces: list[str] = Query(default=[]),
    branch_types: list[str] = Query(default=[]),
    branch_codes: list[str] = Query(default=[]),
):
    return get_overview(start_date, end_date, provinces, branch_types, branch_codes)


@app.get("/api/branches/{branch_code}")
def branch_detail(
    branch_code: str,
    start_date: str | None = None,
    end_date: str | None = None,
):
    result = get_branch_detail(branch_code, start_date, end_date)
    if result is None:
        raise HTTPException(status_code=404, detail="Şube veya seçilen dönem bulunamadı.")
    return result


@app.get("/api/comparison")
def comparison(
    branch_codes: list[str] = Query(default=[]),
    start_date: str | None = None,
    end_date: str | None = None,
):
    return get_comparison(branch_codes, start_date, end_date)


@app.get("/api/analysis")
def analysis(
    start_date: str | None = None,
    end_date: str | None = None,
    branch_codes: list[str] = Query(default=[]),
):
    return get_analysis(start_date, end_date, branch_codes or None)


# AI Danışman endpoint'i bilinçli olarak eklenmemiştir.
# Kullanıcı, daha sonra kendi LLM entegrasyonunu bu katmana bağlayacaktır.
