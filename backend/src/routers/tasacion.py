import re
from math import ceil, floor
from statistics import median
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.catalogs import EstadoVehiculo, VehiculoVersion
from src.models.tasacion import TasacionProspecto
from src.models.user import User
from src.models.vehiculo import Vehiculo
from src.schemas.tasacion import TasacionProspectoOut, TasacionSimularIn, TasacionSimularOut

router = APIRouter(prefix="/tasacion", tags=["tasacion"])

_guard = Depends(require_roles("Sales", "Management", "TenantAdmin"))


def _round_clp(value: int, step: int = 10000) -> int:
    return int(round(value / step) * step)


def _estado_prospecto(db: Session) -> EstadoVehiculo:
    estado = db.scalar(select(EstadoVehiculo).where(EstadoVehiculo.code == "PROSPECTO"))
    if estado is None:
        raise HTTPException(status_code=500, detail="Estado PROSPECTO no está en el catálogo")
    return estado


def _parse_prices_from_html(html: str) -> list[int]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    candidates = re.findall(r"\$\s*([\d\.,]{5,})", text)
    prices: list[int] = []
    for raw in candidates:
        value = int(re.sub(r"[^\d]", "", raw) or "0")
        if 1_000_000 <= value <= 200_000_000:
            prices.append(value)
    return prices[:40]


def _extract_price(text: str) -> int | None:
    match = re.search(r"\$\s*([\d\.,]{5,})", text)
    if not match:
        return None
    value = int(re.sub(r"[^\d]", "", match.group(1)) or "0")
    if 1_000_000 <= value <= 200_000_000:
        return value
    return None


def _parse_listing_candidates(html: str, base_url: str) -> list[tuple[int, str]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    # Chileautos listados suelen venir con enlaces a /vehiculos/... y precio en el mismo bloque.
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if "/vehiculos/" not in href:
            continue

        url = urljoin(base_url, href)
        if url in seen:
            continue

        block = a
        for _ in range(3):
            if block is None:
                break
            text = block.get_text(" ", strip=True)
            price = _extract_price(text)
            if price is not None:
                candidates.append((price, url))
                seen.add(url)
                break
            block = block.parent

        if len(candidates) >= 80:
            break

    return candidates


def _select_representative_url(prices: list[int], listing_candidates: list[tuple[int, str]]) -> str | None:
    if not prices or not listing_candidates:
        return None

    target = median(prices)
    best = min(listing_candidates, key=lambda item: abs(item[0] - target))
    return best[1]


def _percentile(sorted_values: list[int], p: float) -> float:
    if not sorted_values:
        return 0.0
    index = (len(sorted_values) - 1) * p
    lo = floor(index)
    hi = ceil(index)
    if lo == hi:
        return float(sorted_values[lo])
    weight = index - lo
    return float(sorted_values[lo] * (1 - weight) + sorted_values[hi] * weight)


def _filter_outliers(prices: list[int]) -> list[int]:
    if len(prices) < 6:
        return prices
    sorted_prices = sorted(prices)
    q1 = _percentile(sorted_prices, 0.25)
    q3 = _percentile(sorted_prices, 0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return prices
    low = max(500_000, int(q1 - (1.5 * iqr)))
    high = int(q3 + (1.5 * iqr))
    filtered = [v for v in prices if low <= v <= high]
    return filtered if filtered else prices


def _try_scrape_market_prices(query: str) -> tuple[list[int], str | None]:
    if not settings.TASACION_SCRAPING_ENABLED:
        return [], None

    if settings.TASACION_MARKET_PROVIDER != "chileautos":
        return [], None

    url = settings.TASACION_CHILEAUTOS_SEARCH_URL.format(query=quote_plus(query))
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        )
    }
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            listing_candidates = _parse_listing_candidates(response.text, str(response.url))
            listing_prices = [price for price, _ in listing_candidates]
            prices = listing_prices or _parse_prices_from_html(response.text)
            representative_url = _select_representative_url(prices, listing_candidates)
            return prices, representative_url or url
    except Exception:
        return [], url


def _build_market_query(version: VehiculoVersion, anio: int, ppu: str) -> str:
    modelo = version.modelo
    marca = modelo.marca
    return f"{marca.nombre} {modelo.nombre} {version.nombre} {anio} {ppu}".strip()


def _historical_internal_prices(db: Session, version_id: int, anio: int) -> list[int]:
    prospectos = db.scalars(
        select(TasacionProspecto.precio_mercado)
        .where(TasacionProspecto.version_id == version_id)
        .order_by(TasacionProspecto.created_at.desc())
        .limit(120)
    ).all()

    vehiculos_exact_year = db.scalars(
        select(Vehiculo.precio_venta_pactado)
        .where(Vehiculo.version_id == version_id)
        .where(Vehiculo.anio == anio)
        .where(Vehiculo.precio_venta_pactado >= 1_000_000)
        .order_by(Vehiculo.created_at.desc())
        .limit(120)
    ).all()

    vehiculos_near_year = db.scalars(
        select(Vehiculo.precio_venta_pactado)
        .where(Vehiculo.version_id == version_id)
        .where(Vehiculo.anio.between(anio - 2, anio + 2))
        .where(Vehiculo.precio_venta_pactado >= 1_000_000)
        .order_by(Vehiculo.created_at.desc())
        .limit(120)
    ).all()

    combined: list[int] = []
    for value in [*prospectos, *vehiculos_exact_year, *vehiculos_near_year]:
        if 1_000_000 <= value <= 200_000_000:
            combined.append(value)

    return combined[:180]


def _heuristic_base_price(body: TasacionSimularIn) -> int:
    year_factor = max(0, body.anio - 2010)
    km_blocks = max(0, body.km // 10_000)
    base = 6_000_000 + (year_factor * 450_000) - (km_blocks * 120_000)
    return max(4_000_000, min(base, 120_000_000))


def _estimate_prices(db: Session, version: VehiculoVersion, body: TasacionSimularIn, ppu: str) -> tuple[int, int, int, str, str, int, str | None]:
    query = _build_market_query(version, body.anio, ppu)
    raw_prices, scrape_url = _try_scrape_market_prices(query)
    filtered_prices = _filter_outliers(raw_prices)

    source = "scraping_chileautos"
    confidence_note = ""

    if len(filtered_prices) < 5:
        historical = _filter_outliers(_historical_internal_prices(db, version.id, body.anio))
        if historical:
            filtered_prices = historical
            source = "fallback_interno"
            confidence_note = " Scraping externo no disponible; se usó histórico interno."

    if len(filtered_prices) < 3:
        heuristic_price = _heuristic_base_price(body)
        precio_mercado = _round_clp(heuristic_price)
        precio_retoma = _round_clp(int(precio_mercado * 0.9))
        precio_publicacion_sugerido = _round_clp(int(precio_mercado * 1.04))
        return (
            precio_mercado,
            precio_retoma,
            precio_publicacion_sugerido,
            "fallback_heuristico",
            (
                "Estimación de contingencia (baja confianza). "
                "No hubo comparables externos ni histórico interno suficiente."
            ),
            0,
            scrape_url,
        )

    km_penalty = max(0.75, 1 - ((body.km // 10_000) * 0.012))
    mercado_base = median(filtered_prices)
    precio_mercado = _round_clp(int(mercado_base * km_penalty))
    precio_retoma = _round_clp(int(precio_mercado * 0.9))
    precio_publicacion_sugerido = _round_clp(int(precio_mercado * 1.04))
    return (
        precio_mercado,
        precio_retoma,
        precio_publicacion_sugerido,
        source,
        (
            f"Estimación basada en {len(filtered_prices)} referencias filtradas "
            f"de {len(raw_prices)} capturadas.{confidence_note}"
        ),
        len(filtered_prices),
        scrape_url,
    )


def _to_out(p: TasacionProspecto) -> TasacionProspectoOut:
    return TasacionProspectoOut(
        id=p.id,
        ppu=p.ppu,
        km=p.km,
        precio_mercado=p.precio_mercado,
        precio_retoma=p.precio_retoma,
        precio_publicacion_sugerido=p.precio_publicacion_sugerido,
        fuente=p.fuente,
        observacion=p.observacion,
        sample_size=p.sample_size,
        estado_code=p.estado.code,
        captador=p.captador.nombre,
    )


@router.post("/simular", response_model=TasacionSimularOut, dependencies=[_guard])
def simular_tasacion(
    body: TasacionSimularIn,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> TasacionSimularOut:
    ppu = body.ppu.strip().upper()
    referencia_url = body.referencia_url.strip() if body.referencia_url else None
    version = db.get(VehiculoVersion, body.version_id)
    if version is None:
        raise HTTPException(status_code=400, detail="Versión de vehículo inválida")
    precio_mercado, precio_retoma, precio_publicacion_sugerido, fuente, observacion, sample_size, scrape_url = _estimate_prices(db, version, body, ppu)
    final_url = referencia_url or scrape_url

    prospecto = TasacionProspecto(
        tenant_id=tenant_id,
        estado_id=_estado_prospecto(db).id,
        captador_user_id=current.id,
        version_id=version.id,
        ppu=ppu,
        km=body.km,
        precio_mercado=precio_mercado,
        precio_retoma=precio_retoma,
        precio_publicacion_sugerido=precio_publicacion_sugerido,
        fuente=fuente,
        observacion=observacion,
        scrape_url=final_url,
        sample_size=sample_size,
    )
    db.add(prospecto)
    db.commit()
    db.refresh(prospecto)

    return TasacionSimularOut(
        prospecto_id=prospecto.id,
        ppu=prospecto.ppu,
        km=prospecto.km,
        precio_mercado=prospecto.precio_mercado,
        precio_retoma=prospecto.precio_retoma,
        precio_publicacion_sugerido=prospecto.precio_publicacion_sugerido,
        fuente=prospecto.fuente,
        observacion=prospecto.observacion or "",
        sample_size=prospecto.sample_size,
        scrape_url=prospecto.scrape_url,
    )


@router.get("/prospectos", response_model=list[TasacionProspectoOut], dependencies=[_guard])
def listar_prospectos(
    mine: bool = False,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> list[TasacionProspectoOut]:
    stmt = select(TasacionProspecto).where(TasacionProspecto.tenant_id == tenant_id)
    if mine:
        stmt = stmt.where(TasacionProspecto.captador_user_id == current.id)
    prospectos = db.scalars(stmt.order_by(TasacionProspecto.created_at.desc()).limit(100)).all()
    return [_to_out(p) for p in prospectos]
