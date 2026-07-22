"""Galería multimedia de la publicación (fotos y video 360), colgada del acta.

Las fotos son material de ESTA recepción/publicación: por eso el recurso vive
bajo el acta y no bajo el vehículo. Gestionan la galería los roles transversales
(Management/TenantAdmin/SuperAdmin) y —mientras el acta no esté cerrada— el
captador, el vendedor o el equipo de la sucursal de venta derivada.
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src.dependencies import get_current_user, get_effective_tenant_id, require_roles
from src.models.acta import ActaFoto, ActaRecepcion
from src.models.catalogs import OrigenFoto
from src.models.user import User
from src.schemas.multimedia import FotoOut, FotoUpdateIn, FotoUrlIn, VideoIn
from src.services import audit_service, storage
from src.utils.youtube import normalizar as normalizar_youtube

router = APIRouter(prefix="/actas", tags=["multimedia"])

_guard = Depends(require_roles("Sales", "Management", "TenantAdmin"))
_ROLES_TRANSVERSALES = ("Management", "TenantAdmin", "SuperAdmin")

URL_CLOUD = "URL_CLOUD"
ARCHIVO = "ARCHIVO"


# ---------------------------------------------------------------- helpers


def _scoped_acta(db: Session, acta_id: int, tenant_id: int) -> ActaRecepcion:
    a = db.get(ActaRecepcion, acta_id)
    if a is None or a.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acta no encontrada")
    return a


def _require_manage(a: ActaRecepcion, user: User) -> None:
    """Autoriza la gestión de la galería/video del acta o lanza 403."""
    if user.role.code in _ROLES_TRANSVERSALES:
        return
    if not a.cerrada and (
        a.captador_user_id == user.id
        or a.vendedor_user_id == user.id
        or (a.derivado and user.sucursal_id == a.sucursal_venta_id)
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Solo administración, el captador o el vendedor pueden gestionar la galería de esta acta.",
    )


def _foto_out(f: ActaFoto) -> FotoOut:
    return FotoOut(
        id=f.id, acta_id=f.acta_id, url=f.url, orden=f.orden,
        es_principal=f.es_principal, origen=f.origen.code,
    )


def _origen(db: Session, code: str) -> OrigenFoto:
    o = db.scalar(select(OrigenFoto).where(OrigenFoto.code == code))
    if o is None:
        raise HTTPException(status_code=500, detail=f"Origen de foto {code} no está en el catálogo")
    return o


def _proximo_orden(db: Session, acta_id: int) -> int:
    ultimo = db.scalar(select(func.max(ActaFoto.orden)).where(ActaFoto.acta_id == acta_id))
    return (ultimo + 1) if ultimo is not None else 0


def _hay_principal(db: Session, acta_id: int) -> bool:
    return db.scalar(
        select(ActaFoto.id).where(ActaFoto.acta_id == acta_id, ActaFoto.es_principal.is_(True))
    ) is not None


def _crear_foto(db: Session, a: ActaRecepcion, url: str, origen_code: str) -> ActaFoto:
    """Crea la foto al final de la galería; la primera del acta queda principal."""
    foto = ActaFoto(
        tenant_id=a.tenant_id, acta_id=a.id, url=url,
        orden=_proximo_orden(db, a.id),
        es_principal=not _hay_principal(db, a.id),
        origen_id=_origen(db, origen_code).id,
    )
    db.add(foto)
    db.flush()
    return foto


def _audit(request: Request, db: Session, a: ActaRecepcion, user: User, accion: str, extra: dict) -> None:
    audit_service.log(
        db, tenant_id=a.tenant_id, user_id=user.id,
        ip=request.client.host if request.client else None,
        entidad="acta_foto", entidad_id=a.id,
        estado_anterior=None, estado_nuevo=None,
        payload={"accion": accion, "acta_id": a.id, **extra},
    )


# ---------------------------------------------------------------- fotos


@router.get("/{acta_id}/fotos", response_model=list[FotoOut], dependencies=[_guard])
def listar_fotos(
    acta_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
) -> list[FotoOut]:
    a = _scoped_acta(db, acta_id, tenant_id)
    return [_foto_out(f) for f in a.fotos]


@router.post(
    "/{acta_id}/fotos",
    response_model=FotoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_guard],
)
def agregar_foto_url(
    acta_id: int,
    body: FotoUrlIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> FotoOut:
    a = _scoped_acta(db, acta_id, tenant_id)
    _require_manage(a, current)

    url = body.url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La URL debe ser http(s).")

    foto = _crear_foto(db, a, url, URL_CLOUD)
    _audit(request, db, a, current, "agregar_foto_url", {"foto_id": foto.id, "origen": URL_CLOUD})
    db.refresh(foto)
    return _foto_out(foto)


@router.post(
    "/{acta_id}/fotos/upload",
    response_model=FotoOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_guard],
)
async def subir_foto(
    acta_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> FotoOut:
    a = _scoped_acta(db, acta_id, tenant_id)
    _require_manage(a, current)

    ext = storage.ext_para_mime(file.content_type)
    if file.content_type not in settings.media_allowed_mime or ext is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado ({file.content_type}). Usa JPEG, PNG o WebP.",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Archivo vacío.")
    if len(content) > settings.MEDIA_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el máximo de {settings.MEDIA_MAX_BYTES // (1024 * 1024)} MB.",
        )

    url = storage.save(tenant_id, content, ext)
    foto = _crear_foto(db, a, url, ARCHIVO)
    _audit(request, db, a, current, "subir_foto", {"foto_id": foto.id, "origen": ARCHIVO})
    db.refresh(foto)
    return _foto_out(foto)


@router.patch("/{acta_id}/fotos/{foto_id}", response_model=FotoOut, dependencies=[_guard])
def actualizar_foto(
    acta_id: int,
    foto_id: int,
    body: FotoUpdateIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> FotoOut:
    a = _scoped_acta(db, acta_id, tenant_id)
    _require_manage(a, current)
    foto = db.get(ActaFoto, foto_id)
    if foto is None or foto.acta_id != a.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada")

    patch = body.model_dump(exclude_unset=True)
    if "orden" in patch:
        foto.orden = patch["orden"]
    if patch.get("es_principal") is True and not foto.es_principal:
        # Desmarcar la principal actual ANTES de marcar la nueva: el índice único
        # parcial no admite dos principales en la misma acta ni por un instante.
        for otra in a.fotos:
            if otra.es_principal:
                otra.es_principal = False
        db.flush()
        foto.es_principal = True
    elif patch.get("es_principal") is False:
        foto.es_principal = False

    db.flush()
    _audit(request, db, a, current, "actualizar_foto", {"foto_id": foto.id, "campos": sorted(patch.keys())})
    db.refresh(foto)
    return _foto_out(foto)


@router.delete(
    "/{acta_id}/fotos/{foto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[_guard],
)
def eliminar_foto(
    acta_id: int,
    foto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> None:
    a = _scoped_acta(db, acta_id, tenant_id)
    _require_manage(a, current)
    foto = db.get(ActaFoto, foto_id)
    if foto is None or foto.acta_id != a.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada")

    era_principal = foto.es_principal
    url, origen_code = foto.url, foto.origen.code
    db.delete(foto)
    db.flush()

    # Si se borró la principal, promover la primera restante para que la galería
    # siempre tenga una imagen destacada.
    if era_principal:
        siguiente = db.scalar(
            select(ActaFoto)
            .where(ActaFoto.acta_id == a.id)
            .order_by(ActaFoto.orden, ActaFoto.id)
            .limit(1)
        )
        if siguiente is not None:
            siguiente.es_principal = True
            db.flush()

    # Los archivos propios se borran del storage; las URLs del cloud no son nuestras.
    if origen_code == ARCHIVO:
        storage.delete(url)

    _audit(request, db, a, current, "eliminar_foto", {"foto_id": foto_id, "origen": origen_code})


# ---------------------------------------------------------------- video


@router.patch("/{acta_id}/video", response_model=VideoIn, dependencies=[_guard])
def actualizar_video(
    acta_id: int,
    body: VideoIn,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_effective_tenant_id),
    current: User = Depends(get_current_user),
) -> VideoIn:
    a = _scoped_acta(db, acta_id, tenant_id)
    _require_manage(a, current)

    raw = (body.video_youtube_url or "").strip()
    if not raw:
        a.video_youtube_url = None
    else:
        normal = normalizar_youtube(raw)
        if normal is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El enlace debe ser un video de YouTube.",
            )
        a.video_youtube_url = normal

    db.flush()
    audit_service.log(
        db, tenant_id=a.tenant_id, user_id=current.id,
        ip=request.client.host if request.client else None,
        entidad="acta_video", entidad_id=a.id,
        estado_anterior=None, estado_nuevo=None,
        payload={"accion": "actualizar_video", "acta_id": a.id, "tiene_video": a.video_youtube_url is not None},
    )
    db.refresh(a)
    return VideoIn(video_youtube_url=a.video_youtube_url)
