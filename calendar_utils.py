from workalendar.america import Colombia
from datetime import date, timedelta
# obtener los días laborales de un mes específico en Colombia
def get_dias_laborales(year, month):
    cal = Colombia()
    dias_laborales = []
    dia = date(year, month, 1)

    while dia.month == month:
       
        if cal.is_working_day(dia):
            dias_laborales.append(dia)
       
        elif dia.weekday() == 5: 
            dias_laborales.append(dia)
        dia += timedelta(days=1)

    return dias_laborales