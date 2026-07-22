from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "EffiCarBroker"
    API_V1_PREFIX: str = "/api/v1"

    # Base de datos
    DATABASE_URL: str = "postgresql+psycopg://efficar:efficar_dev@db:5432/efficarbroker"

    # JWT
    JWT_SECRET: str = "change-me-in-prod-super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS: lista separada por comas de orígenes permitidos
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Seed
    SEED_DEFAULT_PASSWORD: str = "admin123"
    # Datos operacionales y 2º tenant de DEMO: solo para dev/pruebas.
    # En producción se deja en false → la base queda con catálogos + maestras
    # + el tenant real y sus usuarios, sin captaciones/vehículos/tenant demo.
    SEED_DEMO_DATA: bool = False

    # Media / storage de fotos de la galería
    # MEDIA_ROOT: directorio en disco donde se guardan los archivos subidos.
    # MEDIA_URL_BASE: prefijo de URL bajo el que se sirven (montado en main.py).
    MEDIA_ROOT: str = "/app/media"
    MEDIA_URL_BASE: str = "/media"
    MEDIA_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB por archivo
    # Tipos MIME de imagen aceptados en la subida (todo enum queda fuera de literales sueltos).
    MEDIA_ALLOWED_MIME: str = "image/jpeg,image/png,image/webp"

    # PWA / identidad de app por tenant (manifest e iconos host-aware).
    # Identidad por defecto cuando el Host no mapea a ningún tenant (dev/staging).
    PWA_APP_NAME: str = "EffiCarBroker"
    PWA_THEME_COLOR: str = "#222732"  # brand.dark
    PWA_BACKGROUND_COLOR: str = "#ffffff"
    # Directorio de caché en disco de los iconos generados (por tenant+tamaño+variante+hash del logo).
    PWA_ICON_CACHE_ROOT: str = "/app/media/_app_icons"
    # El backoffice se sirve por tenant en `<prefix><slug><suffix>` (ej.
    # `efficar-vendemostuautomovil.effi4tech.cl`). La identidad PWA host-aware extrae
    # el `slug` del Host para resolver el tenant (la multitenancy de la app es por JWT,
    # no por `dominio`, así que el dominio del backoffice NO es `Tenant.dominio`).
    APP_HOST_PREFIX: str = "efficar-"
    APP_HOST_SUFFIX: str = ".effi4tech.cl"

    # Tasacion / scraping
    TASACION_SCRAPING_ENABLED: bool = True
    TASACION_MARKET_PROVIDER: str = "chileautos"
    TASACION_CHILEAUTOS_SEARCH_URL: str = "https://www.chileautos.cl/vehiculos/?q={query}"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def media_allowed_mime(self) -> set[str]:
        return {m.strip() for m in self.MEDIA_ALLOWED_MIME.split(",") if m.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
