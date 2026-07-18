from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import summarize

app = FastAPI(title="geeknews-summary")
app.include_router(summarize.router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # FastAPI 기본 422 -> 계약 봉투 (400 + {"error"})로 변환.
    # 계약은 error가 참이기만 하면 되므로 필드별 상세 대신 일반 메시지 줌
    return JSONResponse(status_code=400, content={"error": "잘못된 요청입니다."})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # 라우터가 던지는 HTTPException도 같은 {"error"} 봉투로 통일
    # 기본은 {"detail"}
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
