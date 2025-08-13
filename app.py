import pandas as pd
import streamlit as st
from scheduler import asignar_turnos_con_descanso as asignar_turnos
from extras import (
    registrar_horas_extra,
    generar_pdf_horas_extra,
    enviar_correo_horas_extra_agrupado,
    registrar_dia_familia,
    generar_pdf_dia_familia,
    enviar_correo_dia_familia_agrupado,
    generar_pdf_permiso,
    enviar_correo_permiso,
    cargar_registros,
    enviar_correo_vacaciones
)
from datetime import datetime, timedelta
from io import BytesIO
from empleados import EMPLEADOS_POR_AREA

from correos import CORREOS_JEFES
# Constantes para archivos
ARCHIVO_DIA_FAMILIA = "dia_familia.json"
# Función para obtener los días de la semana
def obtener_dia(fecha):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return dias[pd.to_datetime(fecha).weekday()]
# Función para generar el archivo Excel para descarga
def generar_excel_descarga(df, sheet_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

#titulo de la aplicación
def main():
    st.set_page_config(page_title="Sistema de Turnos", layout="wide")
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("logo.png", width=200)
    with col2:
        st.markdown("""
        <style>
            body {
                background-color: #e6f0ff !important;
            }
            .stApp {
                background-color: #f4f9ff !important;
            }
        </style>
        <div style='text-align: center; padding: 20px 10px; font-family: Arial, Helvetica, sans-serif;'>
            <h1 style='color:#19277F; margin-bottom: 10px;'>MUELLES Y FRENOS SIMON BOLIVAR<br>Sistema de Turnos y Registros</h1>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
# Crear pestañas para las diferentes funcionalidades
    tabs = st.tabs(["Turnos", "Tiempo Extra"])
# Asignar turnos
    with tabs[0]:
        st.markdown("<h3 style='color: #19277F;'>Asignar Turnos ⏰</h3>", unsafe_allow_html=True)
# Selección de empleados
        area = st.selectbox("Área de trabajo", ["Seleccione un área"] + list(EMPLEADOS_POR_AREA.keys()))
        empleados_predefinidos = "\n".join(EMPLEADOS_POR_AREA.get(area, [])) if area != "Seleccione un área" else ""
        empleados_input = st.text_area("Lista de empleados (uno por línea), Puedes agregar o borrar empleados.", value=empleados_predefinidos)
        empleados = [e.strip() for e in empleados_input.split("\n") if e.strip()]
# Selección de año y mes
        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("Año", min_value=2023, max_value=2100, value=datetime.now().year)
        with col2:
            month = st.number_input("Mes", min_value=1, max_value=12, value=datetime.now().month)
# Selección de horarios
        horarios_predefinidos = [
            {"nombre": "7:00 AM - 16:00 PM", "horas": 9.0},
            {"nombre": "7:30 AM - 16:15 PM", "horas": 8.75},
            {"nombre": "7:30 AM - 17:00 PM", "horas": 9.5},
            {"nombre": "8:00 AM - 12:00 PM", "horas": 4.0},
            {"nombre": "7:30 AM - 17:15 PM", "horas": 9.75},
            {"nombre": "8:00 AM - 11:30 AM", "horas": 3.5},
            {"nombre": "8:00 AM - 13:00 PM", "horas": 5.0},
            {"nombre": "8:00 AM - 14:00 PM", "horas": 6.0},
            {"nombre": "8:00 AM - 15:00 PM", "horas": 7.0},
            {"nombre": "8:00 AM - 16:00 PM", "horas": 8.0},
            {"nombre": "8:00 AM - 16:45 PM", "horas": 8.75},
            {"nombre": "8:00 AM - 16:30 PM", "horas": 8.5},
            {"nombre": "8:00 AM - 17:00 PM", "horas": 9.0},
            {"nombre": "8:00 AM - 17:30 PM", "horas": 9.5},
            {"nombre": "8:00 AM - 18:00 PM", "horas": 10.0},
            {"nombre": "9:00 AM - 12:30 PM", "horas": 3.5},
            {"nombre": "9:00 AM - 14:00 PM", "horas": 5.0},
            {"nombre": "9:00 AM - 18:00 PM", "horas": 9.0},
            {"nombre": "9:30 AM - 18:00 PM", "horas": 8.5},
            {"nombre": "10:00 AM - 18:00 PM", "horas": 8.0}
        ]

        horarios_opciones_display = [h["nombre"] for h in horarios_predefinidos]
        horarios_mapping = {h["nombre"]: h for h in horarios_predefinidos}
# Selección de horarios de lunes a jueves
        horarios_seleccionados_nombres = st.multiselect("Selecciona los horarios de trabajo de Lunes a Jueves", horarios_opciones_display)
        horarios_lun_jue = [horarios_mapping[n] for n in horarios_seleccionados_nombres]
# Selección de horarios de viernes
        horarios_viernes_nombres = st.multiselect("Selecciona los horarios de trabajo del Viernes (pueden rotar)", horarios_opciones_display)
        horarios_viernes = [horarios_mapping[n] for n in horarios_viernes_nombres]
# Selección de si trabajan los sábados
        trabajan_sabado = st.checkbox("¿Estos empleados trabajan los sábados?")
        horarios_seleccionadossabado = []
        if trabajan_sabado:
            horarios_seleccionadossabado_nombres = st.multiselect(
                "Selecciona los horarios de trabajo para el Sábado (rotarán cada semana)",
                horarios_opciones_display,
            )
            horarios_seleccionadossabado = [horarios_mapping[nombre] for nombre in horarios_seleccionadossabado_nombres]
# Selecciona si algún empleado tiene el Día de la Familia con su fecha
        dia_familia = st.checkbox("Algún empleado tiene el Día de la Familia?")
        empleados_dia_familia_dict = {}
        if dia_familia:
            empleados_dia_familia = st.multiselect("Selecciona los empleados que tienen el Día de la Familia", empleados)
            for empleado in empleados_dia_familia:
                fecha = st.date_input(f"Fecha del Día de la Familia para {empleado}", datetime.now(), key=f"fam_{empleado}")
                empleados_dia_familia_dict[empleado] = fecha
# Selecciona si algún empleado está de vacaciones con su fecha de inicio y fin
        vacaciones = st.checkbox("¿Algún empleado está de vacaciones?")
        empleados_vacaciones_dict = {}
        if vacaciones:
            empleados_vacaciones = st.multiselect("Selecciona los empleados que están de vacaciones", empleados)
            for empleado in empleados_vacaciones:
                inicio = st.date_input(f"Inicio vacaciones de {empleado}", datetime.now(), key=f"vac_ini_{empleado}")
                fin = st.date_input(f"Fin vacaciones de {empleado}", datetime.now(), key=f"vac_fin_{empleado}")
                empleados_vacaciones_dict[empleado] = (inicio, fin)
# Selecciona si asignar días de descanso por empleado
        descansos = st.checkbox("¿Asignar uno o varios días de descanso manual por empleado?")
        empleados_descanso_dict = {}
        if descansos:
            empleados_descanso = st.multiselect("Selecciona los empleados que tendrán días de descanso específicos", empleados)
            for empleado in empleados_descanso:
                fechas_descanso = st.date_input(f"Selecciona la(s) fecha(s) de descanso para {empleado}", [], key=f"descanso_{empleado}")
                if isinstance(fechas_descanso, datetime):
                    fechas_descanso = [fechas_descanso]
                empleados_descanso_dict[empleado] = [f.strftime("%Y-%m-%d") for f in fechas_descanso]
# Botón para generar los turnos
        turnos = None
        if st.button("Generar Turnos"):
            if not empleados:
                st.error("Por favor, ingresa al menos un empleado antes de generar los turnos.")
            elif not horarios_lun_jue:
                st.error("Por favor, selecciona al menos un horario de lunes a jueves.")
            else:
                try:
                    turnos = asignar_turnos(
                        empleados,
                        year,
                        month,
                        horarios_lun_jue,
                        trabajan_sabado,
                        horarios_seleccionadossabado,
                        horarios_viernes
                    )
                except Exception as e:
                    st.error(f"Error al asignar turnos: {e}")
                    turnos = {}

                all_turnos = []
                for empleado, lista in turnos.items():
                    for t in lista:
                        fecha_str = t["fecha"]
                        fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                        turno = t["turno"]
                        horas = t["horas"]

                        if dia_familia and empleado in empleados_dia_familia_dict:
                            if fecha_obj == empleados_dia_familia_dict[empleado]:
                                turno = "Día de la Familia"
                                horas = 0

                        if vacaciones and empleado in empleados_vacaciones_dict:
                            inicio, fin = empleados_vacaciones_dict[empleado]
                            if inicio <= fecha_obj <= fin:
                                turno = "Vacaciones"
                                horas = 0

                        if descansos and empleado in empleados_descanso_dict:
                            if fecha_str in empleados_descanso_dict[empleado]:
                                turno = "Descanso"
                                horas = 0

                        horas_ajustadas = max(horas - 0.75, 0)

                        all_turnos.append({
                            "Empleado": empleado,
                            "Fecha": fecha_str,
                            "Turno": turno,
                            "Horas Laboradas": horas_ajustadas,
                            "Almuerzo": "30 minutos",
                            "Desayuno": "15 minutos"
                        })

                df = pd.DataFrame(all_turnos)
                df["Día"] = df["Fecha"].apply(obtener_dia)
                df["Semana"] = pd.to_datetime(df["Fecha"]).dt.isocalendar().week

                resumen_semanal = df.groupby(["Empleado", "Semana"])["Horas Laboradas"].sum().reset_index()
                resumen_semanal.rename(columns={"Horas Laboradas": "Horas Semana"}, inplace=True)

                df = df.merge(resumen_semanal, on=["Empleado", "Semana"], how="left")
                st.session_state["df_turnos"] = df

        if "df_turnos" in st.session_state:
            df = st.session_state["df_turnos"]

# Crear columna de horas totales si no existe
            if "Horas Totales" not in df.columns:
                df["Horas Totales"] = df["Horas Laboradas"] - 0.75

            st.subheader("Turnos Generados")
            st.dataframe(df[[
                "Empleado", "Fecha", "Día", "Turno", "Almuerzo", "Desayuno", "Horas Laboradas", "Horas Totales"
            ]])
# Descargar turnos en Excel
            st.download_button(
                "Descargar Turnos en Excel",
                generar_excel_descarga(
                    df[[
                        "Empleado", "Fecha", "Día", "Turno", "Almuerzo", "Desayuno", "Horas Laboradas", "Horas Totales"
                    ]],
                    "Turnos"
                ),
                file_name=f"Turnos_{year}_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Horas Extra
    with tabs[1]:
        st.markdown("<h3 style='color: #19277F;'>Registrar Tiempo Extra laborado ⏱️</h3>", unsafe_allow_html=True)      

        num = st.number_input("¿Cuántos empleados trabajaron tiempo extra?", 1, 20, 1)
        campos = []

        for i in range(num):
            st.markdown(f"**Empleado #{i+1}**")
            cols = st.columns(4)

            with cols[0]:
                nombre = st.text_input("Nombre empleado", key=f"he_nombre_{i}")
            with cols[1]:
                fecha = st.date_input("Fecha", key=f"he_fecha_{i}")
            with cols[2]:
                col_h, col_m = st.columns(2)
                with col_h:
                    minutos_di = st.number_input("Minutos Diurnos", 0, 59, key=f"he_diurnas_minutos_{i}")
                with col_m:
                    horas_di = st.number_input("Horas Diurnas", 0, 12, key=f"he_diurnas_horas_{i}")
            with cols[3]:
                col_h, col_m = st.columns(2)
                with col_h:
                    minutos_no = st.number_input("Minutos Nocturnos", 0, 59, key=f"he_nocturnas_minutos_{i}")                   
                with col_m:
                    horas_no = st.number_input("Horas Nocturnas", 0, 12, key=f"he_nocturnas_horas_{i}")

            area_he = st.selectbox("Área de trabajo", 
                ["Logistica","Compras","Cartera","Marketing","Mensajeria","Juridica","Gestion Humana","SST","TI"], 
                key=f"he_area_{i}"
            )

            pago = st.selectbox(
                "Medio de pago",
                ["Seleccione un medio de pago", "Nomina", "Tiempo"],
                key=f"he_pago_{i}"
            )

            campos.append((nombre, fecha, horas_no, horas_di, minutos_di, minutos_no, area_he, pago))

        if st.button("Registrar y enviar"):
            registros = []
            for nombre, fecha, horas_no, horas_di, minutos_di, minutos_no, area_he, pago in campos:
                if not nombre or (horas_di == 0 and minutos_di == 0 and horas_no == 0 and minutos_no == 0):
                    st.error("Completa el nombre y al menos una hora o minuto extra.")
                    break

                registro = registrar_horas_extra(
                    empleado=nombre,
                    fecha=fecha,
                    horas_nocturnas=horas_no,
                    horas_diurnas=horas_di,
                    minutos_di=minutos_di,
                    minutos_no=minutos_no,
                    area=area_he,
                    pago=pago
                )
                registros.extend(registro)

            else:  # Se ejecuta solo si no hubo break
                if registros:
                    pdf = generar_pdf_horas_extra(registros)
                    st.download_button(
                        "Descargar PDF Horas Extra",
                        pdf,
                        file_name="horas_extra_.pdf",
                        mime="application/pdf"
                    )
                    enviar_correo_horas_extra_agrupado(registros)
                    st.success("Horas extra registradas y correo enviado.")     


if __name__ == "__main__":
    main()
# Línea decorativa
    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #19277f;">
            <p>© 2025 Muelles y Frenos Simón Bolívar. Todos los derechos reservados.</p>
        </div>
     """, unsafe_allow_html=True)
                      






