import math
import random
from datetime import datetime, timedelta
from collections import defaultdict
from calendar_utils import get_dias_laborales 


def asignar_turnos_con_descanso(empleados, year, month, horarios_lunes_a_viernes, trabajan_sabado=False, horario_sabado=None):
    """
    Asigna turnos a los empleados para un mes dado, incluyendo la asignación de un día
    de descanso al mes por empleado, asegurando que no más de dos empleados
    descansen el mismo día.

    Args:
        empleados (list): Lista de nombres de los empleados.
        year (int): Año para la asignación de turnos.
        month (int): Mes para la asignación de turnos.
        horarios_lunes_a_viernes (list): Lista de horarios posibles para lunes a viernes.
        trabajan_sabado (bool, optional): Indica si los empleados trabajan los sábados. Por defecto False.
                                          Si es True, se intentará asignar un día de descanso al mes.
        horario_sabado (str o list, optional): Horario(s) específico(s) para los sábados si aplican.
                                                Puede ser un string (un solo horario) o una lista (varios horarios para rotar).

    Returns:
        dict: Un diccionario donde las claves son nombres de empleados y los valores son
              listas de diccionarios con 'fecha', 'turno' y 'fecha_obj'.
    """
    turnos = {}
    dias_laborales = get_dias_laborales(year, month)

    # Agrupar días laborales por semana
    dias_por_semana = defaultdict(list)
    for dia in dias_laborales:
        # Excluir domingos por defecto y sábados si no trabajan ese día
        if dia.weekday() == 6:  
            continue
        if dia.weekday() == 5 and not trabajan_sabado: 
            continue
        semana = dia.isocalendar()[1]
        dias_por_semana[semana].append(dia)

    # Dividir empleados en grupos para la rotación de turnos
    mitad = math.ceil(len(empleados) / 2)
    grupo_a = empleados[:mitad]
    grupo_b = empleados[mitad:]

    total_horarios = len(horarios_lunes_a_viernes)
    semana_actual_idx = 0 # Índice para la rotación de horarios por semana

    for empleado in empleados:
        turnos[empleado] = []

    # Asignar turnos semanales
    for semana_num in sorted(dias_por_semana.keys()):
        idx_turno_a = semana_actual_idx % total_horarios
       
        idx_turno_b = (semana_actual_idx + 1) % total_horarios if total_horarios > 1 else idx_turno_a

        turno_base_a = horarios_lunes_a_viernes[idx_turno_a]
        turno_base_b = horarios_lunes_a_viernes[idx_turno_b]

        for grupo, turno_base in [(grupo_a, turno_base_a), (grupo_b, turno_base_b)]:
            for empleado in grupo:
                for dia_obj in dias_por_semana[semana_num]:
                    turno_final = turno_base
                    if dia_obj.weekday() == 5 and trabajan_sabado: # Si es sábado y trabajan los sábados
                        if isinstance(horario_sabado, list) and len(horario_sabado) > 0:
                            # Rotación entre múltiples horarios de sábado
                            idx_sabado = semana_actual_idx % len(horario_sabado)
                            turno_final = horario_sabado[idx_sabado]
                        elif horario_sabado is not None: 
                            turno_final = horario_sabado
                        else: # Si trabajan sábado pero no se especificó un horario 
                            turno_final = "SIN HORARIO"
                    elif dia_obj.weekday() == 5 and not trabajan_sabado: 
                        turno_final = "DIA LIBRE" 

                    turnos[empleado].append({
                        "fecha": dia_obj.strftime("%Y-%m-%d"),
                        "turno": turno_final,
                        "fecha_obj": dia_obj
                    })
        semana_actual_idx += 1

    # Asignar descansos 
    if trabajan_sabado: #Solo asignar descansos si trabajan sábados
        contador_descansos_por_dia = defaultdict(int) # Cuenta cuántos descansos se han asignado a cada fecha
        empleados_con_descanso_asignado = defaultdict(bool) # Rastrea si un empleado ya tiene su descanso del mes
        empleados_ordenados = sorted(empleados)

        for empleado in empleados_ordenados:
            # Si el empleado ya tiene un descanso asignado este mes, lo saltamos
            if empleados_con_descanso_asignado[empleado]:
                continue

            dias_laborables_del_empleado = []
            for t in turnos[empleado]:
                # excluyendo los ya marcados como "DESCANSO", "SIN HORARIO" o "DIA LIBRE"
                if isinstance(t["turno"], str) and \
                   t["turno"].upper() not in ["DESCANSO", "SIN HORARIO", "DIA LIBRE"]:
                    dias_laborables_del_empleado.append(t)

            # Agrupar los días laborables del empleado por semana
            turnos_por_semana_empleado = defaultdict(list)
            for d in dias_laborables_del_empleado:
                semana_iso = d["fecha_obj"].isocalendar()[1]
                turnos_por_semana_empleado[semana_iso].append(d)
                descanso_asignado_este_empleado = False

            # Primero, buscamos semanas donde el empleado trabajó 6 días           
            semanas_con_6_dias = [s for s, d in turnos_por_semana_empleado.items() if len(d) == 6]         
            # revisar las semanas con 6 días, si no, todas las semanas donde trabajó
            semanas_a_revisar = sorted(semanas_con_6_dias if semanas_con_6_dias else list(turnos_por_semana_empleado.keys()))

            for semana_iso in semanas_a_revisar:
                dias_de_la_semana_candidatos = turnos_por_semana_empleado[semana_iso]

                # Ordenar los días : primero los que tienen menos descansos asignados
                dias_de_la_semana_candidatos_ordenados = sorted(
                    dias_de_la_semana_candidatos,
                    key=lambda d: contador_descansos_por_dia[d["fecha"]]
                )

                for dia_candidato in dias_de_la_semana_candidatos_ordenados:
                    fecha_candidata_str = dia_candidato["fecha"]

                    # Solo asigna si hay menos de 2 descansos ya en esa fecha
                    if contador_descansos_por_dia[fecha_candidata_str] < 2:
                        # Encontrar y actualizar el turno original del empleado
                        for turno_del_empleado in turnos[empleado]:
                            if turno_del_empleado["fecha"] == fecha_candidata_str:
                                turno_del_empleado["turno"] = "DESCANSO"
                                contador_descansos_por_dia[fecha_candidata_str] += 1
                                empleados_con_descanso_asignado[empleado] = True
                                descanso_asignado_este_empleado = True
                                break # Salir del bucle interno (ya se asignó el descanso para este día)
                    
                    if descanso_asignado_este_empleado:
                        break # Salir del bucle de días (ya se asignó el descanso para este empleado)
                
                if descanso_asignado_este_empleado:
                    break # Salir del bucle de semanas (ya se asignó el descanso para este empleado)
    
    return turnos