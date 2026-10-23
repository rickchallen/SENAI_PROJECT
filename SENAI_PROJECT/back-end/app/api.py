import logging
import os
import time
from typing import Any

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import get_session
from app.domain import DomainError
from app.services import clubs, league, market, players
from app.validation import (
    club_sort,
    match_filters,
    path_id,
    player_filters,
    transaction_filters,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
)
logger = logging.getLogger("liga.api")


app = FastAPI(
    title="Liga de Futebol API",
    version="1.0.0",
    description="API REST para gerenciamento de jogadores, clubes, mercado e partidas.",
)

origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Accept"],
)


@app.middleware("http")
async def secure_request_logging(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request method=%s path=%s status=500",
            request.method,
            request.url.path,
        )
        response = JSONResponse(
            status_code=500,
            content={"message": "Falha interna ao processar a requisição."},
        )
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exception: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code,
        content={"message": exception.message},
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    _: Request, __: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"message": "Corpo ou parâmetro da requisição inválido."},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"message": "A operação conflita com dados existentes."},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    _: Request, exception: StarletteHTTPException
) -> JSONResponse:
    message = (
        exception.detail
        if isinstance(exception.detail, str)
        else "Recurso não encontrado."
    )
    return JSONResponse(status_code=exception.status_code, content={"message": message})


@app.get("/api/v1/players")
def list_players(request: Request, session=Depends(get_session)):
    return players.list_players(session, player_filters(request))


@app.get("/api/v1/players/{player_id}")
def get_player(
    player_id: str,
    session=Depends(get_session),
):
    return players.get_player_payload(session, path_id(player_id))


@app.post("/api/v1/players", status_code=201)
def create_player(
    body: dict[str, Any],
    response: Response,
    session=Depends(get_session),
):
    result = players.create_player(session, body)
    response.headers["Location"] = f"/api/v1/players/{result['id']}"
    return result


@app.put("/api/v1/players/{player_id}")
def update_player(
    player_id: str,
    body: dict[str, Any],
    session=Depends(get_session),
):
    return players.update_player(session, path_id(player_id), body)


@app.patch("/api/v1/players/{player_id}/condition")
def update_player_condition(
    player_id: str,
    body: dict[str, Any],
    session=Depends(get_session),
):
    return players.update_condition(session, path_id(player_id), body)


@app.delete("/api/v1/players/{player_id}", status_code=204)
def delete_player(
    player_id: str,
    session=Depends(get_session),
):
    players.delete_player(session, path_id(player_id))
    return Response(status_code=204)


@app.get("/api/v1/clubs")
def list_clubs(
    request: Request,
    session=Depends(get_session),
):
    return clubs.list_clubs(session, club_sort(request))


@app.post("/api/v1/clubs", status_code=201)
def create_club(
    body: dict[str, Any],
    response: Response,
    session=Depends(get_session),
):
    result = clubs.create_club(session, body)
    response.headers["Location"] = f"/api/v1/clubs/{result['id']}"
    return result


@app.get("/api/v1/clubs/{club_id}")
def get_club(
    club_id: str,
    session=Depends(get_session),
):
    return clubs.get_club_payload(session, path_id(club_id))


@app.post("/api/v1/players/{player_id}/buy")
def buy_player(
    player_id: str,
    body: dict[str, Any],
    session=Depends(get_session),
):
    return market.buy_player(session, path_id(player_id), body)


@app.post("/api/v1/players/{player_id}/sell")
def sell_player(
    player_id: str,
    session=Depends(get_session),
):
    return market.sell_player(session, path_id(player_id))


@app.get("/api/v1/clubs/{club_id}/transactions")
def get_transactions(
    club_id: str,
    request: Request,
    session=Depends(get_session),
):
    return market.get_transactions(
        session, path_id(club_id), transaction_filters(request)
    )


@app.get("/api/v1/clubs/{club_id}/transactions/export")
def export_transactions(
    club_id: str,
    request: Request,
    session=Depends(get_session),
):
    csv_content = market.export_transactions(
        session, path_id(club_id), transaction_filters(request)
    )
    return Response(
        content=csv_content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="transacoes-{club_id}.csv"'
        },
    )


@app.get("/api/v1/clubs/{club_id}/lineup")
def get_lineup(
    club_id: str,
    session=Depends(get_session),
):
    return league.get_lineup(session, path_id(club_id))


@app.put("/api/v1/clubs/{club_id}/lineup")
def set_lineup(
    club_id: str,
    body: dict[str, Any],
    session=Depends(get_session),
):
    return league.set_lineup(session, path_id(club_id), body)


@app.post("/api/v1/matches", status_code=201)
def play_match(
    body: dict[str, Any],
    response: Response,
    session=Depends(get_session),
):
    result = league.play_match(session, body)
    response.headers["Location"] = f"/api/v1/matches/{result['id']}"
    return result


@app.get("/api/v1/matches")
def list_matches(
    request: Request,
    session=Depends(get_session),
):
    return league.list_matches(session, match_filters(request))


@app.get("/api/v1/matches/{match_id}")
def get_match(
    match_id: str,
    session=Depends(get_session),
):
    return league.get_match(session, path_id(match_id))


@app.get("/api/v1/standings")
def get_standings(session=Depends(get_session)):
    return league.standings(session)
