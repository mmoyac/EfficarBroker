"""Generación del documento de firma corporativo (2 hojas), fiel al acta real
de vendemostuautomovil.com.

Hoja 1: ACTA DE RECEPCIÓN DIGITAL.
Hoja 2: ORDEN DE VENTA.

Encabezado común con datos del tenant (logo, razón social, RUT, giro, teléfono,
web) y la dirección de la sucursal de origen. Si el tenant no tiene logo, se
reserva el espacio sin romper el layout.
"""

import base64
from datetime import date
from io import BytesIO

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from src.models.acta import ActaRecepcion
from src.models.tenant import Tenant
from src.models.vehiculo import Vehiculo
from src.utils.comision import calcular_comision, calcular_comision_neta, calcular_liquidacion

BRAND_YELLOW = HexColor("#FFD701")
SECTION_BG = HexColor("#5f6b7a")
LIGHT = HexColor("#e7edf3")
MARGIN = 36

_MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha_larga(d: date) -> str:
    return f"{_DIAS[d.weekday()]}, {d.day} de {_MESES[d.month - 1]} de {d.year}"


def _clp(n: int | None) -> str:
    return f"${(n or 0):,}".replace(",", ".")


def _decode_logo(logo: str | None) -> ImageReader | None:
    """Solo soporta data URI base64 (sin dependencias de red / CSP)."""
    if not logo or not logo.startswith("data:"):
        return None
    try:
        _, b64 = logo.split(",", 1)
        return ImageReader(BytesIO(base64.b64decode(b64)))
    except Exception:
        return None


class _Doc:
    def __init__(self, acta: ActaRecepcion, tenant: Tenant | None):
        # El documento se arma desde el ACTA: refleja el cliente, el checklist
        # y la orden de venta de ESA recepción. `v` es la ficha física del auto,
        # compartida por todas las recepciones del mismo vehículo.
        self.a = acta
        self.v = acta.vehiculo
        self.t = tenant
        self.buffer = BytesIO()
        self.c = canvas.Canvas(self.buffer, pagesize=A4)
        self.w, self.h = A4
        self.y = self.h
        self.c.setTitle(f"acta-orden-{self.v.ppu}-{acta.id}.pdf")

    # --- primitives ---
    def text(self, x: float, s: str, size: int = 9, bold: bool = False, color: Color = black) -> None:
        self.c.setFillColor(color)
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        self.c.drawString(x, self.y, s)

    def section(self, titulo: str) -> None:
        self.y -= 18
        self.c.setFillColor(SECTION_BG)
        self.c.rect(MARGIN, self.y - 4, self.w - 2 * MARGIN, 16, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont("Helvetica-Bold", 9)
        self.c.drawString(MARGIN + 6, self.y, titulo)
        self.y -= 14

    def field(self, label: str, value: str, x: float = MARGIN + 6, label_w: float = 120) -> None:
        self.c.setFillColor(black)
        label_up = label.upper()
        self.c.setFont("Helvetica-Bold", 8)
        self.c.drawString(x, self.y, label_up)
        # Posiciona el valor tras el ancho fijo o el ancho real de la etiqueta (evita solaparse).
        lw = self.c.stringWidth(label_up, "Helvetica-Bold", 8)
        self.c.setFont("Helvetica", 8)
        self.c.drawString(x + max(label_w, lw + 8), self.y, value or "-")

    def two_col(self, l1: str, v1: str, l2: str, v2: str) -> None:
        self.field(l1, v1, x=MARGIN + 6, label_w=90)
        self.field(l2, v2, x=self.w / 2 + 6, label_w=90)
        self.y -= 13

    def row(self, label: str, value: str) -> None:
        self.field(label, value)
        self.y -= 13

    # --- header ---
    def header(self, titulo: str) -> None:
        self.y = self.h - 20
        # Barra de marca
        self.c.setFillColor(BRAND_YELLOW)
        self.c.rect(MARGIN, self.h - 70, self.w - 2 * MARGIN, 44, fill=1, stroke=0)
        # Logo del tenant (o espacio reservado)
        logo = _decode_logo(self.t.logo if self.t else None)
        if logo is not None:
            try:
                self.c.drawImage(logo, MARGIN + 6, self.h - 66, width=110, height=36,
                                 preserveAspectRatio=True, mask="auto")
            except Exception:
                pass
        else:
            self.c.setFillColor(black)
            self.c.setFont("Helvetica-Bold", 12)
            self.c.drawString(MARGIN + 10, self.h - 52, (self.t.nombre if self.t else "EffiCarBroker"))
        # Datos de empresa
        razon = (self.t.razon_social if self.t and self.t.razon_social else (self.t.nombre if self.t else "-"))
        rut = self.t.rut if self.t else None
        giro = self.t.giro if self.t else None
        tel = self.t.telefono if self.t else None
        web = self.t.web if self.t else None
        direccion = self.a.sucursal.direccion if self.a.sucursal else None
        self.c.setFillColor(black)
        self.c.setFont("Helvetica", 6.5)
        info = [
            f"{razon}" + (f", RUT: {rut}" if rut else ""),
            giro or "",
            direccion or "",
            (f"Teléfono: {tel}" if tel else "") + (f"   Web: {web}" if web else ""),
        ]
        iy = self.h - 40
        for lineinfo in info:
            if lineinfo:
                self.c.drawString(self.w / 2 - 20, iy, lineinfo)
                iy -= 9
        # Título + PPU + fecha
        self.y = self.h - 92
        self.text(MARGIN, titulo, size=15, bold=True)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.drawRightString(self.w - MARGIN, self.h - 90, f"PPU: {self.v.ppu}")
        self.y -= 12
        self.text(MARGIN, _fecha_larga(date.today()), size=8)
        self.y -= 6

    # --- firmas ---
    def firmas(self, bloques: list[tuple[str, str]]) -> None:
        self.y -= 40
        n = len(bloques)
        seg = (self.w - 2 * MARGIN) / n
        for i, (titulo, sub) in enumerate(bloques):
            cx = MARGIN + seg * i + seg / 2
            self.c.setStrokeColor(black)
            self.c.line(cx - seg / 2 + 20, self.y, cx + seg / 2 - 20, self.y)
            self.c.setFillColor(black)
            self.c.setFont("Helvetica-Bold", 8)
            self.c.drawCentredString(cx, self.y - 12, titulo)
            self.c.setFont("Helvetica", 7)
            self.c.drawCentredString(cx, self.y - 22, sub)


def _bloque_vehiculo(d: _Doc, v: Vehiculo, a: ActaRecepcion) -> None:
    """Datos del auto. El kilometraje sale del ACTA: varía entre recepciones."""
    km = f"{a.km_ingreso:,}".replace(",", ".")
    d.two_col(
        "Tipo de vehículo", v.tipo_vehiculo.nombre if v.tipo_vehiculo else "-",
        "Color", v.color.nombre if v.color else "-",
    )
    d.two_col("Marca", v.marca_nombre, "Año", str(v.anio))
    d.two_col("Modelo", f"{v.modelo_nombre} {v.version.nombre}".strip(), "Kilometraje", km)
    d.two_col("N° Motor", v.n_motor or "-", "Patente", v.ppu)
    d.two_col(
        "N° Chasis", v.n_chasis or "-",
        "Combustible", v.combustible.nombre if v.combustible else "-",
    )


def _page_acta(d: _Doc) -> None:
    v, a = d.v, d.a
    d.header("ACTA DE RECEPCIÓN DIGITAL")

    d.section("ANTECEDENTES DEL CLIENTE")
    c = a.cliente
    d.two_col("RUT", c.rut, "Fono", c.telefono or "-")
    d.two_col("Nombre", c.nombre, "Email", c.email or "-")
    d.two_col("Domicilio", c.domicilio or "-", "Comuna", c.comuna.nombre if c.comuna else "-")

    d.section("ANTECEDENTES DEL VEHÍCULO")
    _bloque_vehiculo(d, v, a)

    d.section("DOCUMENTOS Y ACCESORIOS DEL VEHÍCULO")
    # cabecera de tabla
    d.c.setFont("Helvetica-Bold", 7)
    d.c.setFillColor(black)
    d.c.drawString(MARGIN + 6, d.y, "Declaración de Aceptación y Recepción")
    d.c.drawString(d.w - 220, d.y, "SÍ")
    d.c.drawString(d.w - 195, d.y, "NO")
    d.c.drawString(d.w - 165, d.y, "Fecha Recep.")
    d.c.drawString(d.w - 95, d.y, "Observaciones")
    d.y -= 12
    fecha_recep = a.fecha_recepcion.strftime("%d-%m-%y")
    for idx, item in enumerate(sorted(a.checklist, key=lambda ci: ci.item.orden), start=1):
        d.c.setFont("Helvetica", 7)
        d.c.drawString(MARGIN + 6, d.y, f"{idx:>2}. {item.item.nombre}")
        d.c.drawString(d.w - 218, d.y, "X" if item.presente else "")
        d.c.drawString(d.w - 193, d.y, "" if item.presente else "X")
        d.c.drawString(d.w - 165, d.y, fecha_recep)
        venc = item.fecha_vencimiento.strftime("%d-%m-%y") if item.fecha_vencimiento else (item.observacion or "")
        d.c.drawString(d.w - 95, d.y, venc[:28])
        d.y -= 12

    d.section("OBSERVACIONES")
    d.y -= 2
    d.c.setFont("Helvetica", 8)
    d.c.setFillColor(black)
    d.c.drawString(MARGIN + 6, d.y, "-")
    d.y -= 6

    d.firmas([
        ("RECEPCIÓN A CARGO DE", a.captador.nombre),
        ("FIRMA CLIENTE", a.cliente.nombre),
        ("HUELLA", a.cliente.rut),
    ])
    d.c.showPage()


_CLAUSULAS = [
    ("PRIMERO", "El plazo de pago del saldo dependerá de la modalidad con la que se cierre el negocio. En caso de crédito "
     "con instituciones de financiamiento automotriz, el plazo máximo de pago será de 10 días hábiles desde la firma del "
     "contrato de compraventa. Si el pago se efectúa en efectivo, vale vista o cheque al día, no será superior a 2 días hábiles."),
    ("SEGUNDO", "La comisión pactada por esta prestación de servicios quedará estipulada en las condiciones del contrato y "
     "será pagada de inmediato, de contado, al momento de finiquitarse la venta. El mandatario queda facultado para retener "
     "dicha comisión del precio de la venta que perciba."),
    ("TERCERO", "La ORDEN DE VENTA tiene una vigencia de 30 días corridos, renovable de forma automática sin necesidad de firma."),
    ("CUARTO", "Vendemostuautomovil.com actúa solamente como intermediario comisionista en esta operación, por lo que "
     "cualquier dificultad que se suscitare en el negocio será exclusiva responsabilidad del comprador y vendedor."),
    ("QUINTO", "Al momento de la firma el mandante deja abonado un monto por concepto de exclusividad. Si el automóvil se "
     "vende de forma externa o el dueño decide no vender, este monto cubre honorarios de fotografía, publicidad y gestión. "
     "En caso de concretar la venta, el monto abonado se descuenta de la comisión pactada."),
    ("SEXTO", "En caso de alteraciones en el precio estipulado en esta orden de venta, se debe autorizar por la parte "
     "mandante a través de correo electrónico."),
]


def _wrap(c: canvas.Canvas, text: str, x: float, y: float, max_w: float, size: int = 7, leading: float = 9) -> float:
    c.setFont("Helvetica", size)
    words = text.split()
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, "Helvetica", size) <= max_w:
            line = test
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def _page_orden(d: _Doc) -> None:
    v, a = d.v, d.a
    d.header("ORDEN DE VENTA")

    d.y -= 6
    razon = (d.t.razon_social if d.t and d.t.razon_social else (d.t.nombre if d.t else "la corredora"))
    d.c.setFont("Helvetica", 8)
    d.c.setFillColor(black)
    _wrap(d.c, f"Autorizo a {razon}, del giro compraventa de automóviles, para que enajene el vehículo de mi "
          f"propiedad y perciba su precio en las condiciones estipuladas a continuación:",
          MARGIN + 6, d.y, d.w - 2 * MARGIN - 12, size=8, leading=10)
    d.y -= 24

    d.section("ANTECEDENTES DEL VEHÍCULO")
    _bloque_vehiculo(d, v, a)

    comision = calcular_comision(a.precio_venta_pactado, a.tipo_comision)
    liquidacion = calcular_liquidacion(a.precio_venta_pactado, a.tipo_comision)
    # El abono es anticipo de comisión: al vender, el cliente paga este saldo.
    neta = calcular_comision_neta(a.precio_venta_pactado, a.tipo_comision, a.exclusividad_abono)
    d.section("CONDICIONES DEL CONTRATO")
    d.two_col(
        "Tipo de comisión", a.tipo_comision.nombre if a.tipo_comision else "-",
        "Vigencia", f"{a.vigencia_dias} días",
    )
    d.two_col("Precio", _clp(a.precio_venta_pactado), "Liquidación de pago", _clp(liquidacion))
    d.two_col("Comisión", _clp(comision), "Abono exclusividad", _clp(a.exclusividad_abono))
    d.two_col("Comisión a pagar al cierre", _clp(neta), "", "")

    d.y -= 10
    for titulo, cuerpo in _CLAUSULAS:
        d.c.setFont("Helvetica-Bold", 7)
        d.c.setFillColor(black)
        d.c.drawString(MARGIN + 6, d.y, f"{titulo}:")
        indent = MARGIN + 6 + d.c.stringWidth(f"{titulo}: ", "Helvetica-Bold", 7)
        d.y = _wrap(d.c, cuerpo, indent, d.y, d.w - MARGIN - indent, size=7, leading=8.5)
        d.y -= 4

    razon_rut = d.t.rut if d.t and d.t.rut else "-"
    d.firmas([
        ("FIRMA MANDANTE", f"{a.cliente.nombre}  {a.cliente.rut}"),
        ("FIRMA EJECUTIVO", a.captador.rut or a.captador.nombre),
        ("FIRMA MANDATARIO", f"{razon}  {razon_rut}"),
    ])
    d.c.showPage()


def build_acta_orden_pdf(acta: ActaRecepcion, tenant: Tenant | None) -> bytes:
    d = _Doc(acta, tenant)
    _page_acta(d)
    _page_orden(d)
    d.c.save()
    return d.buffer.getvalue()
