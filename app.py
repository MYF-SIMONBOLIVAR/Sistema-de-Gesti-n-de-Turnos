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
)
from datetime import datetime
from io import BytesIO
from empleados import EMPLEADOS_POR_AREA
from email_utils import enviar_correo_incapacidad
from correos import CORREOS_JEFES

ARCHIVO_DIA_FAMILIA = "dia_familia.json"
# Generar un archivo Excel para descarga
def generar_excel_descarga(df, sheet_name):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

#Titulo de la página y diseño
def main():
    st.set_page_config(page_title="Sistema de turnos", layout="wide")
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
            <h1 style='color:#19277F; margin-bottom: 10px;'>MUELLES Y FRENOS SIMON BOLIVAR<br>SISTEMA DE TURNOS Y REGISTROS</h1>
           
        </div>""", unsafe_allow_html=True)
# Línea decorativa
    st.markdown("<hr style='border: none; height: 4px; background-color: #fab70e;'>", unsafe_allow_html=True)

    tabs = st.tabs(["Turnos", "Horas Extra"])

#Turnos
    with tabs[0]:
        #titulo de la pestaña
        st.markdown("<h3 style='color: #19277F;'>Asignar Turnos ⏰</h3>", unsafe_allow_html=True)

        #Campos para ingresar datos de los empleados, área de trabajo, año, mes y horarios
        area = st.selectbox("Área de trabajo", ["Seleccione un área"] + list(EMPLEADOS_POR_AREA.keys()))
        empleados_predefinidos = "\n".join(EMPLEADOS_POR_AREA.get(area, [])) if area != "Seleccione un área" else ""
        empleados_input = st.text_area("Lista de empleados (uno por línea), Puedes agregar o borrar empleados.", value=empleados_predefinidos)
        empleados = [e.strip() for e in empleados_input.split("\n") if e.strip()]
        col1, col2 = st.columns(2)
        with col1:
            year = st.number_input("Año", min_value=2023, max_value=2100, value=datetime.now().year)
        with col2:
            month = st.number_input("Mes", min_value=1, max_value=12, value=datetime.now().month)

        horarios_predefinidos = [
            "7:00 AM - 4:00 PM","7:00 AM - 4:30 PM", "8:00 AM - 5:30 PM", "7:30AM - 5:00PM", "8:00 AM - 4:30 PM","9:00 AM - 6:00 PM", "9:00 AM - 12:30 PM", "8:00 AM - 2:00 PM","8:00 AM - 11:30 AM", "8:00 AM - 1:00 PM","8:00AM - 4:45PM"
        ]
        horarios_seleccionados = st.multiselect("Selecciona horarios de trabajo de Lunes a Viernes", horarios_predefinidos)
        horario_personalizado = st.text_input("Agregar otro horario (opcional)")
        trabajan_sabado = st.checkbox("¿Estos empleados trabajan los sábados?")

        horarios_seleccionadossabado = []
        if trabajan_sabado:
            horarios_seleccionadossabado = st.multiselect(
                "Selecciona los horarios de trabajo para el Sábado (rotarán cada semana)", 
                horarios_predefinidos,
            )

        horarios_finales = horarios_seleccionados.copy()
        if horario_personalizado.strip():
            horarios_finales.append(horario_personalizado.strip())

        # Botón para generar los turnos
        if st.button("Generar Turnos"):
            if not empleados:
                # Mostrar mensaje de error si no hay empleados
                st.error("Por favor, ingresa al menos un empleado antes de generar los turnos.")
            elif not horarios_finales:
                # Mostrar mensaje de error si no hay horarios
                st.error("Por favor, selecciona o ingresa al menos un horario antes de generar los turnos.")
            else:
                # Asignar turnos sin considerar los días de descanso
                turnos = asignar_turnos(empleados, year, month, horarios_finales, trabajan_sabado, horarios_seleccionadossabado)
                all_turnos = []  # Solo turnos laborales, sin descansos

                for empleado, lista in turnos.items():
                    for t in lista:
                        # Solo agregar los turnos de trabajo, excluyendo los descansos
                        if isinstance(t["turno"], str) and t["turno"].lower() != "descanso":
                            all_turnos.append({"Empleado": empleado, "Fecha": t["fecha"], "Turno": t["turno"]})

                # Guardar los turnos en el DataFrame de la sesión
                st.session_state["df_turnos"] = pd.DataFrame(all_turnos)
                st.session_state["df_descansos"] = None  # No hay descansos

        if "df_turnos" in st.session_state:
            df = st.session_state["df_turnos"]
            st.subheader("Turnos Generados")
            st.dataframe(df)
            # Botón para descargar los turnos en Excel
            st.download_button(
                "Descargar Turnos en Excel",
                generar_excel_descarga(df, "Turnos"),
                file_name=f"Turnos_{year}_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        # Mostrar los días de descanso si hay
        if st.session_state.get("df_descansos") is not None and not st.session_state["df_descansos"].empty:
            df = st.session_state["df_descansos"]
            
            df["Fecha de Descanso"] = pd.to_datetime(df["Fecha de Descanso"])
           
            df = df.sort_values("Fecha de Descanso")
          
            df["Fecha de Descanso"] = df["Fecha de Descanso"].dt.strftime("%Y-%m-%d")
            # Mostrar los días de descanso
            st.subheader("Días de Descanso")
            st.dataframe(df)
            # Botón para descargar los días de descanso en Excel
            st.download_button(
                "Descargar Descansos en Excel",
                generar_excel_descarga(df, "Descansos"),
                file_name=f"Descansos_{year}_{month}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
#Horas Extra
    with tabs[1]:
        #titulo de la pestaña
        st.markdown("<h3 style='color: #19277F;'>Registrar Horas Extra ⏱️</h3>", unsafe_allow_html=True)
       
        #Campo para ingresar el número de empleados que hicieron horas extra
        num = st.number_input("¿Cuántos empleados hicieron horas extra?", 1, 20, 1)
        campos = []
        for i in range(num):
            st.markdown(f"**Empleado #{i+1}**")
            cols = st.columns(4)
            #Campos para ingresar datos del empleado
            with cols[0]: nombre = st.text_input("Nombre empleado", key=f"he_nombre_{i}")
            with cols[1]: fecha = st.date_input("Fecha", key=f"he_fecha_{i}")
            with cols[2]: horas_di = st.number_input("Horas diurnas realizadas", 0, 12, key=f"he_diurnas_{i}")
            with cols[3]: horas_no = st.number_input("Horas nocturnas realizadas", 0, 12, key=f"he_nocturnas_{i}")
            area_he = st.selectbox("Área de trabajo", ["Logistica","Compras","Ventas","Marketing","Mensajeria","Juridica","Gestion Humana","SST","TI"], key=f"he_area_{i}")
            campos.append((nombre, fecha, horas_di, horas_no, area_he))
        #Botón para registrar y enviar horas extra
        if st.button("Registrar y enviar horas extra"):
            registros = []
            for nombre, fecha, hd, hn, area_he in campos:
                if not nombre or (hd == 0 and hn == 0):
                    # Mostrar mensaje de error si falta información
                    st.error("Completa nombre y al menos una hora extra.")
                    break
                registro = registrar_horas_extra(nombre, fecha, hd, hn, area_he)
                registros.extend(registro)
            else:
                if registros:
                    # Generar PDF con los registros de horas extra
                    pdf = generar_pdf_horas_extra(registros)
                    st.download_button(
                        "Descargar PDF Horas Extra",
                        pdf,
                        file_name="horas_extra_.pdf",
                        mime="application/pdf"
                    )
                    # Enviar correo con los registros
                    enviar_correo_horas_extra_agrupado(registros)
                    # Mostrar mensaje de éxito
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
                      



