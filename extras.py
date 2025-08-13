import json
import yagmail
import os
from datetime import datetime
from fpdf import FPDF
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()
# Configuración de correo electrónico.
EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_P = os.getenv("EMAIL_P")  # contraseña del correo.
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")
EMAIL_DESTINATARIO_FAMILIA = os.getenv("EMAIL_DESTINATARIO_FAMILIA")
# Archivos de registros.
ARCHIVO_HORAS_EXTRA = "horas_extra.json"
ARCHIVO_HORAS_EXTRA_NOCTURNAS = "horas_extra_nocturnas.json"
VALOR_HORA_EXTRA_DIURNA = 7736
VALOR_HORA_EXTRA_NOCTURNA = 10831
# Cargar registros guardados.
def cargar_registros(archivo):
    try:
        with open(archivo, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# Guardar registros en JSON
def guardar_registros(archivo, registros):
    with open(archivo, "w") as f:
        json.dump(registros, f, indent=4)


# Registrar horas extra

def registrar_horas_extra(empleado, fecha, horas_nocturnas=0, horas_diurnas=0, minutos_di=0, minutos_no=0, area=None, pago=None):
    registros = []

    # Convertir a decimal para cálculos, pero guardar minutos aparte
    total_horas_di = horas_diurnas + (minutos_di / 60)
    total_horas_no = horas_nocturnas + (minutos_no / 60)

    if total_horas_di > 0:
        registro = {
            "empleado": empleado,
            "fecha": str(fecha),
            "horas": round(total_horas_di, 2),
            "horas_int": horas_diurnas,
            "minutos": minutos_di,
            "tipo": "diurnas",
            "area": area,
            "pago": pago,
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        regs = cargar_registros(ARCHIVO_HORAS_EXTRA)
        regs.append(registro)
        guardar_registros(ARCHIVO_HORAS_EXTRA, regs)
        registros.append(registro)

    if total_horas_no > 0:
        registro = {
            "empleado": empleado,
            "fecha": str(fecha),
            "horas": round(total_horas_no, 2),
            "horas_int": horas_nocturnas,
            "minutos": minutos_no,
            "tipo": "nocturnas",
            "area": area,
            "pago": pago,
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        regs = cargar_registros(ARCHIVO_HORAS_EXTRA_NOCTURNAS)
        regs.append(registro)
        guardar_registros(ARCHIVO_HORAS_EXTRA_NOCTURNAS, regs)
        registros.append(registro)

    return registros


# Enviar correo con horas extra
def enviar_correo_horas_extra_agrupado(registros):
    yag = yagmail.SMTP(EMAIL_REMITENTE, EMAIL_P)
    asunto = "Horas extra registradas"
    cuerpo = "<p>Cordial saludo,<br><br>Se han registrado las siguientes horas extra:</p><ul>"
    total_general = 0

    for r in registros:
        # Verificar si el medio de pago es tiempo, si es así no calcular el valor
        if r.get("pago") == "tiempo":
            continue  # Si el pago es 'tiempo', no se genera valor ni se incluye en el correo

        valor_hora = VALOR_HORA_EXTRA_DIURNA if r["tipo"] == "diurnas" else VALOR_HORA_EXTRA_NOCTURNA
        total = r["horas"] * valor_hora
        total_general += total

        # Mostrar horas y minutos exactos
        tiempo_str = ""
        if r["horas_int"] > 0:
            tiempo_str += f"{r['horas_int']}h "
        if r["minutos"] > 0:
            tiempo_str += f"{r['minutos']}m"

        cuerpo += (
            f"<li>"
            f"<b>{r['empleado']}</b> | "
            f"Área: <b>{r.get('area','N/A')}</b> | "
            f"Pago: <b>{r.get('pago','N/A')}</b> | "
            f"Fecha: <b>{r['fecha']}</b> | "
            f"Tiempo {r['tipo']}: <b>{tiempo_str.strip()}</b> | "
            f"Total: <b>${total:,.0f}</b>"
            f"</li>"
        )

    cuerpo += "</ul>"
    cuerpo += (
        f"<p><b>Total a pagar: ${total_general:,.0f}</b><br>"
        f"Fecha de registro: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b><br><br>"
        "\n\nQuedamos atentos a cualquier comentario o requerimiento adicional."
        "\n\nAtentamente,\nÁrea de TI"
    )

    # Enviar el correo solo si hay horas extra pagadas
    if total_general > 0:
        yag.send(to=EMAIL_DESTINATARIO, subject=asunto, contents=cuerpo)
    else:
        print("No se generaron horas extra pagadas, no se envió el correo.")

# -------------------------------
# Generar PDF con horas extra
def generar_pdf_horas_extra(registros):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Reporte de Horas Extra", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, "Cordial saludo,\nSe informa que se han registrado las siguientes horas extra:")
    pdf.ln(5)

    total_general = 0
    for r in registros:
        valor_hora = VALOR_HORA_EXTRA_DIURNA if r["tipo"] == "diurnas" else VALOR_HORA_EXTRA_NOCTURNA
        total = r["horas"] * valor_hora
        total_general += total
        pdf.cell(0, 10, f"Empleado: {r['empleado']}", ln=True)
        pdf.cell(0, 10, f"Área: {r.get('area','')}", ln=True)
        pdf.cell(0, 10, f"Pago: {r.get('pago','')}", ln=True)
        pdf.cell(0, 10, f"Fecha: {r['fecha']}", ln=True)
        pdf.cell(0, 10, f"Horas {r['tipo']}: {r['horas']} (Total: ${total:,.0f})", ln=True)
        pdf.ln(5)

    pdf.multi_cell(0, 10, f"Total general: ${total_general:,.0f}")
    pdf.multi_cell(0, 10, "Quedamos atentos a cualquier comentario o requerimiento adicional.")
    pdf.cell(0, 10, "Atentamente,\nÁrea de TI", ln=True)

    return pdf.output(dest='S').encode('latin1')
# registrar días de la familia
def registrar_dia_familia(empleado, fecha, area, archivo, correo_em, correo_jefe,firma=None):
    registros = cargar_registros(archivo)
    reg = {
        "empleado": empleado,
        "fecha": str(fecha),
        "area": area,
        "correo": correo_em,
        "correo_jefe": correo_jefe,
        "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "firma": firma.name if firma else None
    }
    registros.append(reg)
    guardar_registros(archivo, registros)
    return reg
# enviar correos electrónicos dia de la familia
def enviar_correo_dia_familia_agrupado(registros):
    yag = yagmail.SMTP(EMAIL_REMITENTE, EMAIL_P)
    asunto = "Días de la Familia registrados"
    cuerpo = "Cordial saludo,\n\nSe han solicitado los siguientes Días de la Familia:\n"
    for r in registros:
        cuerpo += f"\n- {r['empleado']} | Área: {r.get('area','N/A')} | Fecha: {r['fecha']} | Correo empleado: {r['correo']} | Correo Jefe: {r['correo_jefe']}"
        #firma si existe
      
        cuerpo += f" | Firma: {r['firma']}"
    cuerpo += f"\n\nFecha de registro: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}" \
              "\n\nQuedamos atentos a cualquier comentario o requerimiento adicional." \
              "\n\nAtentamente,\nÁrea de TI"
    yag.send(to=EMAIL_DESTINATARIO, subject=asunto, contents=cuerpo)
# generar PDF de días de la familia
def generar_pdf_dia_familia(registros):
    pdf = FPDF()
    pdf.add_page()
    pdf.image("plantillaSM.png", x=0, y=0, w=210, h=297)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Solicitud Día de la Familia", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, "Cordial saludo,\nSe informa que se ha solicitado el día de la familia para los siguientes empleados:")
    pdf.ln(5)
    for r in registros:
        pdf.cell(0, 10, f"Empleado: {r['empleado']}", ln=True)
        pdf.cell(0, 10, f"Área: {r.get('area','')}", ln=True)
        pdf.cell(0, 10, f"Fecha solicitada: {r['fecha']}", ln=True)

        pdf.ln(5)
    pdf.ln(5)
    pdf.multi_cell(0, 10, "Quedamos atentos a cualquier comentario o requerimiento adicional.")
    pdf.cell(0, 10, "Atentamente,\nÁrea de TI", ln=True)
    return pdf.output(dest='S').encode('latin1')
# enviar permisos
def enviar_correo_permiso(registro):
    destinatario = registro["correo_jefe"]
    destinatario_empleado = registro["correo"] 

# Construir asunto
    asunto = f"Solicitud de Permiso - {registro['nombre']}"

# Determinar si hay que especificar horas o minutos
    detalle_tiempo = ""
    if registro["tipo"] == "Medio dia":
        detalle_tiempo = " (aproximadamente 4 horas)"
    elif registro["tipo"] == "Cita medica":
        detalle_tiempo = " (tiempo estimado: en minutos u horas según cita)"

# Cuerpo del correo
    cuerpo = f"""<h3>Solicitud de Permiso</h3>
    <p>Cordial saludo,<br>
    Se informa que se ha solicitado un permiso para el empleado <b>{registro['nombre']}</b>.<br>
    Fecha solicitada: <b>{registro['fecha']}</b><br>
    Tipo de permiso: <b>{registro['tipo']}{detalle_tiempo}</b></p>
    <p>Correo del empleado: <b>{registro['correo']}</b></p>  <!-- Correo del empleado -->"""
    

    if registro.get("pe_motivo"):
        cuerpo += f"<p>Motivo del permiso especial: <b>{registro['pe_motivo']}</b></p>"

    cuerpo += """
    <p>Quedamos atentos a cualquier comentario o requerimiento adicional.</p>
    <p>Atentamente,<br>Área de TI</p>"""

   
    print(f"Correo enviado a: {destinatario}")
    print(f"Asunto: {asunto}")
    print(f"Cuerpo del correo:\n{cuerpo}")

# Enviar
    yag = yagmail.SMTP(EMAIL_REMITENTE, EMAIL_P)
    yag.send(to=destinatario, subject=asunto, contents=cuerpo)


def generar_pdf_permiso(registro):
    pdf = FPDF()
    pdf.add_page()
    pdf.image("plantillaSM.png", x=0, y=0, w=210, h=297)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Solicitud de Permiso", ln=True, align="C")
    pdf.ln(10)

# Texto principal
    pdf.multi_cell(0, 10, f"Cordial saludo,\nSe informa que se ha solicitado un permiso para el empleado {registro['nombre']}.")
    pdf.ln(5)

# Detalle de tiempo
    detalle_tiempo = ""
    if registro["tipo"] == "Medio dia":
        detalle_tiempo = " (aproximadamente 4 horas)"
    elif registro["tipo"] == "Cita medica":
        detalle_tiempo = " (tiempo estimado: en minutos u horas según cita)"

    pdf.cell(0, 10, f"Fecha solicitada: {registro['fecha']}", ln=True)
    pdf.cell(0, 10, f"Tipo de permiso: {registro['tipo']}{detalle_tiempo}", ln=True)

    # Motivo si aplica
    if registro.get("pe_motivo"):
        pdf.multi_cell(0, 10, f"Motivo del permiso especial: {registro['pe_motivo']}")

    pdf.ln(5)
    pdf.multi_cell(0, 10, "Quedamos atentos a cualquier comentario o requerimiento adicional.")
    pdf.cell(0, 10, "Atentamente,", ln=True)
    pdf.cell(0, 10, "Área de TI", ln=True)

    return pdf.output(dest='S').encode('latin1')

def enviar_correo_vacaciones(registro):
    destinatario = registro["correo_jefe"]  # Correo del jefe directo.
    destinatario1 = registro["correo_em"]   # Correo del empleado.
    
    # Asunto y cuerpo del correo.
    asunto = f"Solicitud de Vacaciones - {registro['nombre']}"
    cuerpo = f"""<h3>Solicitud de Vacaciones</h3>
    <p>Cordial saludo,<br>
    Se informa que el empleado <b>{registro['nombre']}</b> ha solicitado sus vacaciones.<br>
    Fecha solicitada: <b>{registro['fecha_inicio']}</b> hasta <b>{registro['fecha_fin']}</b><br>
    <p>Correo del empleado: <b>{registro['correo_em']}</b></p>  <!-- Correo del empleado --> 
    """
    
    cuerpo += """
    <p>Quedamos atentos a cualquier comentario o requerimiento adicional.</p>
    <p>Atentamente,<br>Área de TI</p>"""
    
    



