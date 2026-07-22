# AGENTS.md - Especificación Tecnológica y Estructura de Proyecto

Este documento define la arquitectura tecnológica, el stack de desarrollo y la estructura de directorios unificada para el ecosistema **EffiCarBroker** (Vertical Automotriz del SaaS de Consignación y Corretaje de **Effi4Tech**). Todo el sistema está diseñado para ser desplegado mediante contenedores **Docker** en entornos de desarrollo, staging y producción.

---

## 1. Stack Tecnológico General

El ecosistema se compone de tres capas principales completamente desacopladas y un orquestador asíncrono, asegurando un entorno modular, multi-inquilino (Multi-tenant) y tipado de forma estricta.

### 1.1. Backend API (Core EffiCarBroker)
* **Core:** FastAPI (Python 3.11+).
* **Base de Datos:** PostgreSQL 15+ (Estrategia de aislamiento de datos por fila usando `tenant_id` en todas las tablas transaccionales).
* **ORM:** SQLAlchemy + Alembic para migraciones.
* **Validación de Datos:** Pydantic v2 (Modo Estricto)[cite: 1].

### 1.2. Backoffice Corporativo (Panel de Administración de Clientes)
* **Framework / Tooling:** React 18 + Vite + TypeScript (Strict Mode configurado)[cite: 1].
* **Estilos e Identidad Visual:** Tailwind CSS[cite: 1].
* **Navegación Dinámica (RBAC):** Menú lateral (Sidebar) reactivo construido a partir del rol del usuario autenticado mediante el endpoint `GET /api/v1/navigation/menu`[cite: 1].
* **Gestión de Estado / Consultas:** TanStack Query (React Query) + Axios / Context API[cite: 1].

### 1.3. Landing Page Pública (Catálogo y Captación)
* **Framework:** Next.js 14+ (React) utilizando App Router[cite: 1].
* **Renderizado:** Server-Side Rendering (SSR) y Static Site Generation (SSG) para optimización SEO del catálogo de vehículos[cite: 1].
* **Estilos:** Tailwind CSS (manteniendo consistencia visual con el Backoffice de EffiCarBroker)[cite: 1].

### 1.4. Orquestación y Automatización
* **Motor:** n8n (Integración nativa vía Webhooks con el Backend para la aprobación de contratos y coordinación automatizada de visitas por correo/WhatsApp)[cite: 1].

---

## 2. Estructura de Directorios Multi-Contenedor (Docker)

Se adopta una arquitectura de monorepositorio con contenedores Docker independientes para cada módulo operativo.

```text
efficarbroker-platform/             # Carpeta Principal del Proyecto
│
├── .gitignore
├── README.md
├── docker-compose.yml              # Orquestación de todos los servicios locales
│
├── backend/                        # Módulo del Backend Core (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── src/
│   │   ├── main.py                 # Punto de entrada de FastAPI
│   │   ├── config/                 # Configuración multi-tenant, JWT y variables de entorno
│   │   ├── database.py             # Conexión y sesión de PostgreSQL con filtros por tenant_id
│   │   ├── models/                 # Modelos de SQLAlchemy (Tablas base + Logs de auditoría Append-Only)
│   │   ├── schemas/                # Esquemas de validación de Pydantic (Modo Estricto)
│   │   ├── routers/                # Endpoints divididos por dominios (auth, navigation, vehiculos, liquidaciones)
│   │   ├── services/               # Lógica de negocio pura (cálculos de comisiones cruzadas, bonos por volumen)
│   │   └── utils/                  # Módulos de auditoría e interceptores de logs y scrapers de mercado
│   └── migrations/                 # Scripts de Alembic para versionamiento de BD
│
├── backoffice/                     # Módulo de Administración EffiCarBroker (React + Vite)
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json               # Configuración estricta de TypeScript
│   ├── tailwind.config.js          # Configuración de Tailwind CSS
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── components/             # Componentes de UI compartidos e inyección dinámica del Sidebar Menu
│       ├── context/                # Contextos globales (Autenticación Multi-tenant, Permisos RBAC)
│       ├── hooks/                  # Custom hooks para control de estados y consumo de APIs
│       ├── pages/                  # Vistas del negocio por Rol (Tasación, Recepción, Validaciones, BI/CEO Dashboard)
│       ├── services/               # Clientes de API (Axios configurado con interceptor de Tokens)
│       └── types/                  # Definiciones e interfaces TypeScript estrictas
│
├── landing/                        # Módulo Público / Catálogo de Autos (Next.js)
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── app/                    # Next.js App Router (Páginas públicas, Catálogo dinámico, Formularios)
│       ├── components/             # Componentes UI de la Landing Page
│       └── services/               # Consumo de la API pública del backend para el catálogo filtrado por Tenant
│
└── n8n/                            # Configuración local de n8n para flujos de trabajo
    └── workflows/                  # Archivos JSON con la lógica automatizada de contratos y alertas post día 31
```

---

## 3. Estándares de UI/UX (OBLIGATORIOS para todo código de frontend)

Los ejecutivos de captación/venta operan **desde el móvil y en terreno**. Todo componente, página o modal que se construya o modifique en el `backoffice` (y en la `landing`) **DEBE** cumplir estas condiciones. No son sugerencias: son requisitos de aceptación. Si un cambio de UI no las cumple, no está terminado.

### 3.1. Mobile-first y responsive desde 5" (~320 px)
* **Diseñar primero para móvil** y escalar hacia arriba con breakpoints de Tailwind (`sm:` `md:` `lg:`). El objetivo base de ancho es **320–360 px** (equipos de 5").
* **Prohibido el scroll horizontal de página.** El `body` nunca debe desbordar. Todo contenido ancho (tablas, diagramas, bloques de código) se desplaza **dentro de su propio contenedor** con `overflow-x-auto`.
* **Objetivos táctiles ≥ 44×44 px** en botones, enlaces de acción, íconos accionables y campos de formulario.
* **Espaciado adaptativo:** evitar paddings grandes fijos; usar patrón `p-4 md:p-8` (no `p-8` a secas). Tipografía legible sin zoom.
* Respetar `viewport-fit=cover` y las **safe-areas** (`env(safe-area-inset-*)`) para notch/barras del sistema en la app instalada.

### 3.2. Navegación adaptativa
* El **Sidebar** es fijo solo en `md+`. Bajo `md` se presenta como **drawer off-canvas** con overlay, accesible desde un botón (hamburguesa) en un header móvil.
* El menú por rol (`GET /api/v1/navigation/menu`), el cambio de automotora (`TenantSwitcher`) y el cierre de sesión **deben permanecer accesibles** en la navegación móvil.

### 3.3. Listados: tabla en escritorio, tarjetas en móvil
* Toda vista de listado con `<table>` **DEBE** ofrecer en `<md` una disposición de **tarjetas apiladas** por registro (3–4 campos clave + acciones), conservando la tabla completa en `md+`.
* Piso mínimo no negociable: si aún no hay patrón de tarjetas, la tabla va envuelta en `overflow-x-auto` para no romper la página.

### 3.4. Formularios y modales
* Modales y formularios **usables a 320–360 px**: ancho completo con **scroll interno** cuando el contenido excede el alto; nunca recortar campos ni botones de acción.
* Los grids de formulario colapsan a 1 columna en móvil (`grid-cols-1` → `sm:grid-cols-*`).

### 3.5. PWA (aplicación instalable, multitenant)
* El `backoffice` es una **PWA instalable** (installable + app shell). Todo cambio debe preservar la instalabilidad: `manifest`, service worker registrado y meta-tags no se rompen.
* **Identidad por tenant, resuelta por dominio:** el `manifest` y los iconos se sirven **host-aware desde el backend** (según el `Host` → `Tenant.dominio`), mostrando el **nombre e icono de la automotora** correspondiente, aunque el build de frontend sea único para todos los dominios. No hardcodear "EffiCarBroker" como nombre/icono de app.
* **El service worker NO cachea datos ni respuestas autenticadas:** todo lo bajo `/api/` y `/media/` es NetworkOnly. Sin conexión abre el shell, pero las vistas con datos fallan como sin PWA (no hay offline de datos en esta etapa).
* **Actualización controlada:** tras un deploy se avisa "nueva versión disponible" y se actualiza bajo acción del usuario; **prohibido** recargar de forma silenciosa que descarte un formulario en curso.

### 3.6. Identidad visual y consistencia
* Usar **exclusivamente** la paleta de marca definida en `tailwind.config.js` (`brand.*`: accent `#FFD701`, dark `#222732`, etc.). No introducir colores sueltos ni una librería de UI nueva sin acordarlo.
* Reutilizar componentes existentes en `components/` antes de crear nuevos; mantener el mismo lenguaje visual del backoffice en la landing.

### 3.7. Verificación mínima antes de dar por terminado un cambio de UI
* Revisar la vista a **320–360 px** (sin scroll horizontal de página) y en escritorio.
* Confirmar objetivos táctiles y que modales/tablas/nav cumplen 3.2–3.4.
* Si se tocó algo de PWA: la app sigue siendo instalable y la identidad por dominio no se rompió.