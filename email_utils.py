
import yagmail
import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# enviar correos electrónicos de notificación horas extra
def enviar_correo_extra(nombre_empleado, fecha, horas, email_jefe):
    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)
    asunto = f"Horas extra - {nombre_empleado}"
    cuerpo = f"""<h3>Registro de horas extra</h3>
    <p>Empleado: <b>{nombre_empleado}</b><br>
    Fecha: <b>{fecha}</b><br>
    Horas: <b>{horas}</b></p>"""
    yag.send(to=email_jefe, subject=asunto, contents=cuerpo)

# enviar correos electrónicos de notificación de día de la familia
def enviar_correo_familia(nombre_empleado, fecha, email_jefe):
    yag = yagmail.SMTP(EMAIL, EMAIL_PASSWORD)
    asunto = f"Día de la Familia - {nombre_empleado}"
    cuerpo = f"""<h3>Solicitud de Día de la Familia</h3>
    <p>Empleado: <b>{nombre_empleado}</b><br>
    Fecha: <b>{fecha}</b></p>"""
    yag.send(to=email_jefe, subject=asunto, contents=cuerpo)
