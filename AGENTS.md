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