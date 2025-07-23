import json
import yagmail
import os
from datetime import datetime
from fpdf import FPDF
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

# Configuración de correo electrónico
EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_P = os.getenv("EMAIL_P")  # contraseña del correo
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO")
EMAIL_DESTINATARIO_FAMILIA = os.getenv("EMAIL_DESTINATARIO_FAMILIA")
# Archivos de registros
ARCHIVO_HORAS_EXTRA = "horas_extra.json"
ARCHIVO_HORAS_EXTRA_NOCTURNAS = "horas_extra_nocturnas.json"
VALOR_HORA_EXTRA_DIURNA = 7736
VALOR_HORA_EXTRA_NOCTURNA = 10831
# cargar archivos JSON
def cargar_registros(archivo):
    try:
        with open(archivo, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
# guardar registros en un archivo JSON
def guardar_registros(archivo, registros):
    with open(archivo, "w") as f:
        json.dump(registros, f, indent=4)
# registrar horas extra 
def registrar_horas_extra(empleado, fecha, horas_diurnas=0, horas_nocturnas=0, area=None):
    registros = []
    if horas_diurnas > 0:
        registro = {
            "empleado": empleado,
            "fecha": str(fecha),
            "horas": horas_diurnas,
            "tipo": "diurnas",
            "area": area,
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        regs = cargar_registros(ARCHIVO_HORAS_EXTRA)
        regs.append(registro)
        guardar_registros(ARCHIVO_HORAS_EXTRA, regs)
        registros.append(registro)
    if horas_nocturnas > 0:
        registro = {
            "empleado": empleado,
            "fecha": str(fecha),
            "horas": horas_nocturnas,
            "tipo": "nocturnas",
            "area": area,
            "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        regs = cargar_registros(ARCHIVO_HORAS_EXTRA_NOCTURNAS)
        regs.append(registro)
        guardar_registros(ARCHIVO_HORAS_EXTRA_NOCTURNAS, regs)
        registros.append(registro)
    return registros
# enviar correos electrónicos 
def enviar_correo_horas_extra_agrupado(registros):
    yag = yagmail.SMTP(EMAIL_REMITENTE, EMAIL_P)
    asunto = "Horas extra registrada"
    cuerpo = "<p>Cordial saludo,<br><br>Se han registrado las siguientes horas extra:</p><ul>"
    total_general = 0
    for r in registros:
        total = r["horas"] * (VALOR_HORA_EXTRA_DIURNA if r["tipo"] == "diurnas" else VALOR_HORA_EXTRA_NOCTURNA)
        total_general += total
        cuerpo += (
            f"<li>"
            f"<b>{r['empleado']}</b> | "
            f"Área: <b>{r.get('area','N/A')}</b> | "
            f"Fecha: <b>{r['fecha']}</b> | "
            f"Horas {r['tipo']}: <b>{r['horas']}</b> | "
            f"Total: <b>${total:,.0f}</b>"
            f"</li>"
        )
    cuerpo += "</ul>"
    cuerpo += (
        f"<p><b>Total a pagar: ${total_general:,.0f}</b><br>"
        f"Fecha de registro: <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b><br><br>"
         "\n\nQuedamos atentos a cualquier comentario o requerimiento adicional." \
         "\n\nAtentamente,\nÁrea de TI"
    )
    yag.send(to=EMAIL_DESTINATARIO, subject=asunto, contents=cuerpo)
# generar PDF de horas extra
def generar_pdf_horas_extra(registros):
    pdf = FPDF()
    pdf.add_page()

    # Verificar si la imagen existe antes de intentar cargarla
    imagen_path = "images/plantillaSM.png"
    if os.path.exists(imagen_path):
        try:
            pdf.image(imagen_path, x=0, y=0, w=210, h=297)
        except Exception as e:
            print(f"Error al cargar la imagen: {e}")
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "Reporte de Horas Extra (Imagen no encontrada)", ln=True, align="C")
    else:
        print(f"El archivo de imagen '{imagen_path}' no se encuentra en el directorio.")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "Reporte de Horas Extra (Imagen no encontrada)", ln=True, align="C")
    
    # Títulos y formato
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "Cordial saludo,\nSe informa que se han registrado las siguientes horas extra:")
    pdf.ln(5)

    total_general = 0
    
    # Iterar sobre los registros y agregar los detalles al PDF
    for r in registros:
        # Suponiendo que 'r' tiene las claves 'empleado', 'horas' y 'total'
        empleado = r.get('empleado', 'Desconocido')
        horas_extra = r.get('horas', 0)
        total_horas = r.get('total', 0)

        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Empleado: {empleado}", ln=True)
        pdf.cell(0, 10, f"Horas extra: {horas_extra}", ln=True)
        pdf.cell(0, 10, f"Total horas: {total_horas}", ln=True)
        pdf.ln(5)

        total_general += total_horas

    # Agregar un resumen al final
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, f"Total general de horas extra: {total_general}", ln=True, align="C")
    
    # Guardar el archivo PDF
    pdf_output = "reporte_horas_extra.pdf"
    pdf.output(pdf_output)
    print(f"PDF generado: {pdf_output}")

# registrar días de la familia
def registrar_dia_familia(empleado, fecha, area, archivo):
    registros = cargar_registros(archivo)
    reg = {
        "empleado": empleado,
        "fecha": str(fecha),
        "area": area,
        "registrado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        cuerpo += f"\n- {r['empleado']} | Área: {r.get('area','N/A')} | Fecha: {r['fecha']}"
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
    yag = yagmail.SMTP(EMAIL_REMITENTE, EMAIL_P)
    asunto = f"Solicitud de Permiso - {registro['nombre']}"
    cuerpo = f"""<h3>Solicitud de Permiso</h3>
    <p>Cordial saludo,<br>
    Se informa que se ha solicitado un permiso para el empleado <b>{registro['nombre']}</b>.<br>
    Fecha solicitada: <b>{registro['fecha']}</b><br>
    Tipo de permiso: <b>{registro['tipo']}</b></p>
    <p>Quedamos atentos a cualquier comentario o requerimiento adicional.</p>
    <p>Atentamente,<br>Área de TI</p>"""
    yag.send(to=EMAIL_DESTINATARIO, subject=asunto, contents=cuerpo)
# generar PDF de permisos
def generar_pdf_permiso(registro):
    pdf = FPDF()
    pdf.add_page()
    pdf.image("plantillaSM.png", x=0, y=0, w=210, h=297)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Solicitud de Permiso", ln=True, align="C")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Cordial saludo,\nSe informa que se ha solicitado un permiso para el empleado {registro['nombre']}.")
    pdf.ln(5)
    pdf.cell(0, 10, f"Fecha solicitada: {registro['fecha']}", ln=True)
    pdf.cell(0, 10, f"Tipo de permiso: {registro['tipo']}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 10, "Quedamos atentos a cualquier comentario o requerimiento adicional.")
    pdf.cell(0, 10, "Atentamente,\nÁrea de TI", ln=True)
    return pdf.output(dest='S').encode('latin1')
