import logging
from contextlib import asynccontextmanager

from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import settings
from src.core.db import close_db, connect_db, ensure_indexes, get_db
from src.core.errors import CommonErrorCodes, IFlowError
from src.core.log import setup_logging
from src.modules.auth.router import router as auth_router
from src.modules.currency.router import router as currency_router
from src.modules.odin.router import router as odin_router
from src.modules.profile.router import router as profile_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    await connect_db()
    await ensure_indexes()
    logger.info("iflow-api started")
    yield
    await close_db()
    logger.info("iflow-api stopped")


app = FastAPI(title="iflow-api", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_response(
    code: str, message: str, category: str, status: int
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "category": category,
                "status": status,
            }
        },
    )


@app.exception_handler(IFlowError)
async def _iflow_error_handler(_request: Request, exc: IFlowError):
    return JSONResponse(status_code=exc.status, content=exc.body())


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(
    _request: Request, exc: RequestValidationError
):
    messages = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err["loc"] if l != "body")
        msg = err["msg"]
        messages.append(f"{loc}: {msg}" if loc else msg)
    return _error_response(
        code=CommonErrorCodes.VALIDATION_ERROR,
        message="; ".join(messages),
        category="validation",
        status=422,
    )


@app.exception_handler(InvalidId)
async def _invalid_object_id_handler(_request: Request, exc: InvalidId):
    return _error_response(
        code=CommonErrorCodes.INVALID_RESOURCE_ID,
        message=f"Invalid resource ID: {exc}",
        category="validation",
        status=400,
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(_request: Request, exc: HTTPException):
    return _error_response(
        code=CommonErrorCodes.HTTP_ERROR,
        message=str(exc.detail),
        category="unexpected",
        status=exc.status_code,
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return _error_response(
        code=CommonErrorCodes.UNEXPECTED_ERROR,
        message="An unexpected error occurred.",
        category="unexpected",
        status=500,
    )


app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(profile_router, prefix="/api", tags=["Profile"])
app.include_router(currency_router, prefix="/api", tags=["Currency"])
app.include_router(odin_router, prefix="/api/odin", tags=["ODIN"])


@app.get("/api/health", tags=["Health"])
async def health():
    db = get_db()
    await db.command("ping")
    return {"status": "ok"}
