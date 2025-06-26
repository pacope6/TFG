from gurobipy import *
import random

def definir_var_ceros(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, SaturdayList, y, c3, c4, c3prev, c4prev, g5, h6, WeekendDates, PrevShifts, PrevDays, j, z, model):
    
    """Se definen las variables = 0 para evitar problemas en la heurística"""
    
    
    if modelo == '3':
        for n in Physicians:
            for d in Dates:
                for s in Shifts:
                    for k in Locations:
                        x[n,d,s,k].Start = 0
            
        for n in Physicians:
            for d in Dates:
                for s in Shifts:
                    t[n,d,s].Start = 0
            
        for n in Physicians:
            for d in Dates:
                for k in Locations:
                    l[n,d,k].Start = 0

        for n in Physicians:
            for d in Dates:
                o[n,d].Start = 0
        
        if modelo == '2':
            for n in Physicians:
                for d in SaturdayList:
                    y[n,d].Start = 0

        for n in Physicians:
                for d in Dates:
                    for s in Shifts:
                        c3[n,d,s].Start = 0   
        
        for n in Physicians:
                for d in Dates:
                    c4[n,d].Start = 0
        
        for n in Physicians:
                for d in PrevShifts:
                    for s in Shifts:
                        c3prev[n,d,s].Start = 0 
        
        for n in Physicians:
                for d in PrevDays:
                    c4prev[n,d].Start = 0

        if modelo == '2':
            for n in Physicians:
                    for d in Dates:
                        for s in Shifts:
                            g5[n,d,s].Start = 0  

        for n in Physicians:
                if modelo == '2':
                    for d in SaturdayList:
                        h6[n,d].Start = 0
                elif modelo == '3':
                    for d in WeekendDates:
                        h6[n,d].Start = 0
                
        for n in Physicians:
                for j_index in [7,8,9]:
                    j[j_index,n].Start = 0
        
        
    if modelo == '1':
        # 1. Variables binarias principales (x, z, o)
        for n in Physicians:
            for d in Dates:
                # Variable x (asignación completa)
                for s in Shifts:
                    for k in Locations:
                        x[n,d,s,k].Start = 0
                
                # Variables z (turnos en fines de semana) y o (días trabajados)
                z[n,d].Start = 0
                o[n,d].Start = 0
        
        # 2. Variable y (fines de semana completos)
        for n in Physicians:
            for d in SaturdayList:
                y[n,d].Start = 0
        
        # 3. Variables auxiliares continuas
        # c3 (turnos consecutivos)
        for n in Physicians:
            for d in Dates:
                for s in Shifts:
                    c3[n,d,s].Start = 0
        
        # c4 (días consecutivos)
        for n in Physicians:
            for d in Dates:
                c4[n,d].Start = 0
        
        # c3prev (turnos consecutivos históricos)
        for n in Physicians:
            for d in PrevShifts:
                for s in Shifts:
                    c3prev[n,d,s].Start = 0
        
        # c4prev (días consecutivos históricos)
        for n in Physicians:
            for d in PrevDays:
                c4prev[n,d].Start = 0
        
        # 4. Variables especiales
        # g5 (asignaciones no deseadas - variable escalar)
        g5.Start = 0
        
        # h6 (violaciones de fines de semana)
        for n in Physicians:
            for d in SaturdayList:
                h6[n,d].Start = 0
        
        # j (variables de holgura)
        for n in Physicians:
            for j_index in [7,8,9]:
                j[j_index,n].Start = 0
    

    model.update()


def heuristica_ordenada(Physicians, Phy_Night_Pre, Night_Consec_Pre, ConsecutiveDays_Heur, Dates, 
                        LabDates, UnavailablePhysicians, Shifts, Locations, alpha, UndesiredPhysicians, 
                        Num_Incomp, SaturdayList):

    """
        Se genera una solución factible del modelo con el algoritmo heurístico

        Input: Conjuntos y parámetros

        Output: set Var_Pre con las variables x[n,d,s,k] que se deben iniciar; es decir, 
            turnos asignados
    """
            
    Var_Pre = set() #set de variables x preiniciadas

    #Physicians disponibles desde el día anterior
    #Phy_left_e = Physicians.copy(), hay que tener en cuenta la info. del turno previo
    Phy_left = [n for n in Physicians if n not in Phy_Night_Pre]

    #Variables para contabilizar
    TurnosN_Consecutivos = {} #nº de turnos consecutivos
    Turnos_Totales = {}
    Max_TurnosN_Consecutivos = {} #si está en el límite (3) vale 1, si no 0
    Fines_Semana = {} #número de fines de semana trabajados
    Dias_Consecutivos = {} 
    Max_Dias_Consecutivos = {}
    Undesired_Shift = {}
    Incomp_Dia_Siguiente = {}
    for n in Physicians:
        TurnosN_Consecutivos[n] = Night_Consec_Pre[n] #info previa noches consec.
        Dias_Consecutivos[n] = ConsecutiveDays_Heur[n] #info previa días consec.
        Turnos_Totales[n] = 0
        Fines_Semana[n] = 0
        Undesired_Shift[n] = 0
        Incomp_Dia_Siguiente[n] = 0
        if TurnosN_Consecutivos[n] < 3:
            Max_TurnosN_Consecutivos[n] = 0
        else: 
            Max_TurnosN_Consecutivos[n] = 1
        if Dias_Consecutivos[n] < 5:
            Max_Dias_Consecutivos[n] = 0
        else: 
            Max_Dias_Consecutivos[n] = 1


    for d in Dates:
        if d in LabDates: #diario

            for n in Physicians:
                if any((n,Dates[Dates.index(d)+1],s1) in UnavailablePhysicians for s1 in Shifts):
                        Incomp_Dia_Siguiente[n] = 1
                else:
                        Incomp_Dia_Siguiente[n] = 0
                
                if d != '0Mon':
                    Dias_Consecutivos[n] = 0
                    c=0
                    i=1 #empezamos mirando el día anterior
                    while c == 0:
                        if any((n, Dates[Dates.index(d) - i], s, k) in Var_Pre for k in Locations for s in Shifts):
                            Dias_Consecutivos[n] += 1
                            i += 1
                        else:
                            c=1
                    if Dias_Consecutivos[n] < 5:
                        Max_Dias_Consecutivos[n] = 0
                    else: 
                        Max_Dias_Consecutivos[n] = 1

            for s in Shifts:
                Phy_nec = sum(alpha[1, d, s, k] for k in Locations) #número necesario para el turno
                Phy_left2 = [n for n in Phy_left if (n,d,s) not in UnavailablePhysicians] #disponibilidad

                for n in Phy_left2: 
                    if (n,d,s) in UndesiredPhysicians:
                        Undesired_Shift[n] = 1
                    else:
                        Undesired_Shift[n] = 0
                    
                if s == 'Early' or s == 'Late':
                    Phy_ordenados = sorted(Phy_left2, key=lambda n: (Max_Dias_Consecutivos[n], 
                                                                    Undesired_Shift[n],
                                                                    -Incomp_Dia_Siguiente[n],
                                                                    Turnos_Totales[n], 
                                                                    -Num_Incomp[n],
                                                                    random.random()
                                                                    ))
                elif s == 'Night':
                    for n in Phy_left2:
                        if TurnosN_Consecutivos[n] < 3:
                            Max_TurnosN_Consecutivos[n] = 0
                        else: 
                            Max_TurnosN_Consecutivos[n] = 1

                    Phy_ordenados = sorted(Phy_left2, key=lambda n: (Max_Dias_Consecutivos[n],
                                                                    Max_TurnosN_Consecutivos[n],
                                                                    Undesired_Shift[n],
                                                                    -Incomp_Dia_Siguiente[n],
                                                                    Turnos_Totales[n], 
                                                                    -Num_Incomp[n],
                                                                    random.random()
                                                                    ))

                #print(Phy_ordenados)
                Phy_selected = Phy_ordenados[:Phy_nec]
                #print(Phy_selected)

                if s == 'Early':
                    Phy_left = [n for n in Phy_left if n not in Phy_selected]
                    Phy_Early = Phy_selected.copy()

                elif s == 'Late':
                    Phy_left = [n for n in Physicians if (n not in Phy_selected and n not in Phy_Early)]

                elif s == 'Night':
                    Phy_left = [n for n in Physicians if n not in Phy_selected]
                    for n in Physicians:
                        if n not in Phy_selected:
                            TurnosN_Consecutivos[n] = 0
                            Max_TurnosN_Consecutivos[n] = 0

                assignment = {}
                index = 0
                for k in Locations:
                    group_size = alpha[1, d, s, k]  # Tamaño del grupo para esta ubicación
                    assignment[k] = Phy_selected[index:index + group_size]
                    index += group_size  # Mover el índice para el siguiente grupo
                for k, group in assignment.items():
                    #print(f"Location {k}: {group}")
                    for n in group:
                        Var_Pre.add((n,d,s,k))
                        
                        if s == 'Early' or s == 'Late':
                            Turnos_Totales[n] += 1
                            #Dias_Consecutivos[n] += 1
                        elif s == 'Night':
                            Turnos_Totales[n] += 2
                            #Dias_Consecutivos[n] += 1
                            TurnosN_Consecutivos[n] += 1
                #print(Var_Pre)
        elif d in SaturdayList: #fin de semana, saltamos el domingo

            for n in Physicians:
                if d != '3Sat':
                    if any((n,Dates[Dates.index(d)+2],s1) in UnavailablePhysicians for s1 in Shifts): #incomp. el lunes
                            Incomp_Dia_Siguiente[n] = 1
                    else:
                            Incomp_Dia_Siguiente[n] = 0
                

                Dias_Consecutivos[n] = 0
                c=0
                i=1 #empezamos mirando el día anterior
                while c == 0:
                    if any((n, Dates[Dates.index(d) - i], s, k) in Var_Pre for k in Locations for s in Shifts):
                        Dias_Consecutivos[n] += 1
                        i += 1
                    else:
                        c=1
                if Dias_Consecutivos[n] < 4: #vamos a asignar dos días
                    Max_Dias_Consecutivos[n] = 0
                else: 
                    Max_Dias_Consecutivos[n] = 1

            for s in ['Early','Night']:
                Phy_nec = sum(alpha[1, d, s, k] for k in Locations) #número necesario para el turno
                Phy_left2 = [n for n in Phy_left if ((n,d,s) not in UnavailablePhysicians and (n,Dates[Dates.index(d)+1],s) not in UnavailablePhysicians)] #disponibilidad

                for n in Phy_left2: 
                    if ((n,d,s) in UndesiredPhysicians or (n,Dates[Dates.index(d)+1],s) in UndesiredPhysicians):
                        Undesired_Shift[n] = 1
                    else:
                        Undesired_Shift[n] = 0
                    
                if s == 'Early' or s == 'Late':
                    Phy_ordenados = sorted(Phy_left2, key=lambda n: (Max_Dias_Consecutivos[n], 
                                                                    Undesired_Shift[n],
                                                                    Fines_Semana[n],
                                                                    -Incomp_Dia_Siguiente[n],
                                                                    Turnos_Totales[n], 
                                                                    -Num_Incomp[n],
                                                                    random.random()
                                                                    ))
                elif s == 'Night':
                    for n in Phy_left2:
                        if TurnosN_Consecutivos[n] < 2: #vamos a asignar dos consecutivas
                            Max_TurnosN_Consecutivos[n] = 0
                        else: 
                            Max_TurnosN_Consecutivos[n] = 1

                    Phy_ordenados = sorted(Phy_left2, key=lambda n: (Max_Dias_Consecutivos[n],
                                                                    Max_TurnosN_Consecutivos[n],
                                                                    Undesired_Shift[n],
                                                                    Fines_Semana[n],
                                                                    -Incomp_Dia_Siguiente[n],
                                                                    Turnos_Totales[n], 
                                                                    -Num_Incomp[n],
                                                                    random.random()
                                                                    ))

                #print(Phy_ordenados)
                Phy_selected = Phy_ordenados[:Phy_nec]
                #print(Phy_selected)

                if s == 'Early' or s == 'Late':
                    Phy_left = [n for n in Physicians if n not in Phy_selected]

                elif s == 'Night':
                    Phy_left = [n for n in Physicians if n not in Phy_selected]
                    for n in Physicians:
                        if n not in Phy_selected:
                            TurnosN_Consecutivos[n] = 0
                            Max_TurnosN_Consecutivos[n] = 0

                assignment = {}
                index = 0
                for k in Locations:
                    group_size = alpha[1, d, s, k]  # Tamaño del grupo para esta ubicación
                    assignment[k] = Phy_selected[index:index + group_size]
                    index += group_size  # Mover el índice para el siguiente grupo
                for k, group in assignment.items():
                    #print(f"Location {k}: {group}")
                    for n in group:
                        
                        if s == 'Early':
                            Var_Pre.add((n,d,s,k))
                            Var_Pre.add((n,d,'Late',k))
                            Var_Pre.add((n,Dates[Dates.index(d)+1],s,k))
                            Var_Pre.add((n,Dates[Dates.index(d)+1],'Late',k))

                            Turnos_Totales[n] += 4
                            Fines_Semana[n] += 1
                            #Dias_Consecutivos[n] += 1
                        elif s == 'Night':
                            Var_Pre.add((n,d,s,k))
                            Var_Pre.add((n,Dates[Dates.index(d)+1],s,k))

                            Turnos_Totales[n] += 4
                            Fines_Semana[n] += 1
                            #Dias_Consecutivos[n] += 1
                            TurnosN_Consecutivos[n] += 2
                #print(Var_Pre)

    return Var_Pre

def iniciar_turnos(Var_Pre, x, model):

    "Se inician las variables x dada una solución de la heurística"

    for var in Var_Pre:
        n = var[0]
        d = var[1]
        s = var[2]
        k = var[3]
        x[n,d,s,k].Start = 1

    model.update()

def iniciar_variables(
        modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, WeekendDates, SaturdayList, y, h6, 
        model, beta3, c3, LastShift, c3prev, PrevShifts, beta, c4, ConsecutiveDays, c4prev, PrevDays, j, 
        UndesiredPhysicians, g5, PhysiciansCompleteWeekend, z):
    
    "Se definen el resto de variables (no x) tras una iteración de la heurística"

    if modelo == '3':
        for n in Physicians:
            for d in Dates:
                for s in Shifts:
                    for k in Locations:
                        if x[n,d,s,k].Start == 1:
                            t[n,d,s].Start = 1
                            l[n,d,k].Start = 1
                            o[n,d].Start = 1
                            if d in WeekendDates:
                                if modelo == '2':
                                    if d in SaturdayList:
                                        y[n,d].Start = 1
                                    else:
                                        indice = Dates.index(d)
                                        y[n,Dates[indice-1]].Start = 1
                                elif modelo == '3':
                                    if d in SaturdayList: #si se trabaja el sábado
                                        if any(x[n,Dates[Dates.index(d)+1],s1,k1].Start == 1 for s1 in Shifts for k1 in Locations):
                                            0
                                        else: #y no se trabaja el domingo
                                            h6[n,Dates[Dates.index(d)+1]].Start = 1
                                        
                                    else: #si se trabaja el domingo
                                        if any(x[n,Dates[Dates.index(d)-1],s1,k1].Start == 1 for s1 in Shifts for k1 in Locations):
                                            0
                                        else: #y no se trabaja el sábado
                                            h6[n,Dates[Dates.index(d)-1]].Start = 1

        model.update()

                    
        for n in Physicians:
            for s in Shifts:
                for d in range(len(Dates[:-beta3[n,s]])):
                        c3[n,Dates[d],s].Start = max(sum(t[n, d2, s].Start for d2 in Dates[d:d+beta3[n,s]+1]) - beta3[n,s], 0)
            
                for d in range(LastShift[n,s][1]):
                    if LastShift[n,s][1] != 0:
                        c3prev[n,PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]],s].Start = max(- beta3[n,s] + LastShift[n,s][1]-d + sum(t[n, d2, s].Start for d2 in Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)]), 0)
            
            for d in range(len(Dates[:-beta[4,n]])):
                c4[n,Dates[d]].Start = max(sum(o[n, d2].Start for d2 in Dates[d:d+beta[4,n]+1]) - beta[4,n], 0)

            for d in range(ConsecutiveDays[n]):
                if ConsecutiveDays[n] != 0:
                    
                    c4prev[n,PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]].Start =max(ConsecutiveDays[n]-d + sum(o[n, d2].Start for d2 in Dates[0:(beta[4,n]+1-ConsecutiveDays[n]+d)]) - beta[4,n],0)

            j[7,n].Start = max(beta[7,n] - sum(t[n,d,'Early'].Start + t[n,d,'Late'].Start + 2*t[n,d,'Night'].Start for d in Dates),0)

            j[8,n].Start = max(-beta[8,n] + sum(t[n,d,'Early'].Start + t[n,d,'Late'].Start + 2*t[n,d,'Night'].Start for d in Dates),0)
            
            if modelo == '2':
                j[9,n].Start = max(sum(y[n,d].Start for d in SaturdayList) - beta[9,n],0)
            elif modelo == '3':
                j[9,n].Start = max(sum((1/2)*(o[n,d].Start + h6[n,d].Start + o[n,Dates[Dates.index(d)+1]].Start + h6[n,Dates[Dates.index(d)+1]].Start) for d in SaturdayList) - beta[9,n],0)
        
        if modelo == '2':
            for (n,d,s) in UndesiredPhysicians:
                g5[n,d,s].Start = max(t[n,d,s].Start,0)

        if modelo == '2':
            for n in PhysiciansCompleteWeekend:
                for w in range(len(SaturdayList)):
                    '''print(n,w)
                    print(y[n,SaturdayList[w]].Start)
                    print(o[n,SaturdayList[w]].Start,o[n,Dates[7*(w+1)-1]].Start)'''
                    h6[n, SaturdayList[w]].Start = max(y[n,SaturdayList[w]].Start * 2 - o[n,SaturdayList[w]].Start - o[n,Dates[7*(w+1)-1]].Start, 0)


        model.update()
    if modelo == '1':
        for n in Physicians:
            for d in Dates:
                for s in Shifts:
                    for k in Locations:
                        if x[n,d,s,k].Start == 1:
                            o[n,d].Start = 1
                            if d in SaturdayList:
                                y[n,d].Start = 1
                            else:
                                # En modelo 1, solo SaturdayList se maneja para y, así que no ponemos lógicas para domingo
                                pass  
                            if d in WeekendDates:
                                if s in ['Early',]:
                                    z[n,d].Start = 1
                                    x[n,d,'Late',k].Start = 1
                                elif s in ['Late']:
                                    z[n,d].Start = 1
                                    x[n,d,'Early',k].Start = 1

        model.update()

        # Asignación de variables auxiliares para Modelo1 (versión corregida)
        for n in Physicians:
            for s in Shifts:
                # Para fechas sin considerar LastShift (caso general)
                for d_idx in range(len(Dates) - beta3[n, s]):
                    current_date = Dates[d_idx]
                    end_idx = min(d_idx + beta3[n, s] + 1, len(Dates))
                    # suma de asignaciones del turno s en todas las ubicaciones
                    c3[n, current_date, s].Start = max(
                        sum(sum(x[n, Dates[d2_idx], s, k].Start for k in Locations if (n, Dates[d2_idx], s, k) in x)
                            for d2_idx in range(d_idx, end_idx)) - beta3[n, s], 
                        0
                    )
                
                # Para fechas previas con LastShift
                if LastShift[n, s][1] != 0:
                    for d in range(min(LastShift[n, s][1], len(PrevShifts))):
                        idx_prev = d + len(PrevShifts) - LastShift[n, s][1]
                        date_range = min(beta3[n, s] + 1 - LastShift[n, s][1] + d, len(Dates))
                        c3prev[n, PrevShifts[idx_prev], s].Start = max(
                            -beta3[n, s] + LastShift[n, s][1] - d + sum(x[n, d, s, k].Start for d in Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)] for k in Locations),0
                        )

            # Máximo días consecutivos de trabajo
            for d_idx in range(len(Dates) - beta[4, n]):
                current_date = Dates[d_idx]
                end_idx = min(d_idx + beta[4, n] + 1, len(Dates))
                c4[n, current_date].Start = max(
                    sum(o[n, Dates[d2_idx]].Start for d2_idx in range(d_idx, end_idx) if (n, Dates[d2_idx]) in o) - beta[4, n],
                    0
                )
            
            # Máximo días consecutivos considerando histórico
            if ConsecutiveDays[n] != 0:
                for d in range(min(ConsecutiveDays[n], len(PrevDays))):
                    idx_prev = d + len(PrevDays) - ConsecutiveDays[n]
                    date_range = min(beta[4, n] + 1 - ConsecutiveDays[n] + d, len(Dates))
                    c4prev[n, PrevDays[idx_prev]].Start = max(
                        ConsecutiveDays[n] - d + sum(
                            o[n, Dates[d2_idx]].Start for d2_idx in range(0, date_range) if (n, Dates[d2_idx]) in o
                        ) - beta[4, n],
                        0
                    )

            # Variables de holgura para límites de turnos (versión corregida)
            total_shifts = sum(
                sum(x[n, d, 'Early', k].Start for k in Locations if (n, d, 'Early', k) in x) +
                sum(x[n, d, 'Late', k].Start for k in Locations if (n, d, 'Late', k) in x) +
                2 * sum(x[n, d, 'Night', k].Start for k in Locations if (n, d, 'Night', k) in x)
                for d in Dates if (n, d) in o  # Verificamos que el médico tenga asignación en esa fecha
            )
            
            j[7, n].Start = max(beta[7, n] - total_shifts, 0)
            j[8, n].Start = max(total_shifts - beta[8, n], 0)
            j[9, n].Start = max(
                sum(y[n, d].Start for d in SaturdayList if (n, d) in y) - beta[9, n],
                0
            )

        # Asignación para g5 con verificación completa
        g5.Start = sum(
            sum(x[n, d, s, k].Start for k in Locations if (n, d, s, k) in x)
            for (n, d, s) in UndesiredPhysicians if (n, d, s) in UndesiredPhysicians
        )

        # Asignación para h6 con verificación completa
        for n in PhysiciansCompleteWeekend:
            for w in range(len(SaturdayList)):
                if w >= len(SaturdayList):
                    continue
                d = SaturdayList[w]
                if 7*(w+1)-1 >= len(Dates):
                    continue
                siguiente_dia = Dates[7*(w+1)-1]
                
                if (n, d) in o and (n, siguiente_dia) in o and (n, d) in y:
                    h6[n, d].Start = abs(o[n, d].Start + o[n, siguiente_dia].Start - 2 * y[n, d].Start)
                else:
                    h6[n, d].Start = 0  # Valor por defecto si no existe la asignación

        model.update()

        

        # En modelo 1 g5 es variable escalar, no vector
        # Y no hay asignación de g5 como vector, ni h6 en fines de semana distintos a SaturdayList
        # Si quieres agregar lógica para g5 u h6, especifica la regla

def calcular_funcion_objetivo(
        modelo, omega, c3, c3prev, c4, c4prev, Physicians, Dates, Shifts, PrevShifts, PrevDays, g5, h6, 
        SaturdayList, j, t, UndesiredPhysicians, WeekendDates):
    
    """Se calcula la función objetivo para diferentes modelos"""

    if modelo == '3':
        valor = omega[3]*(sum(c3[n,d,s].Start for n in Physicians for d in Dates for s in Shifts) + sum(c3prev[n,d,s].Start for n in Physicians for d in PrevShifts for s in Shifts)) + omega[4]*(sum(c4[n,d].Start for n in Physicians for d in Dates) + sum(c4prev[n,d].Start for n in Physicians for d in PrevDays)) + omega[5]*sum(t[n,d,s].Start for (n,d,s) in UndesiredPhysicians) + omega[6]*sum(h6[n,d].Start for n in Physicians for d in WeekendDates) + omega[7]*sum(j[7,n].Start for n in Physicians) + omega[8]*sum(j[8,n].Start for n in Physicians) + omega[9]*sum(j[9,n].Start for n in Physicians)
        #*sum(t[n,d,s] for (n,d,s) in UndesiredPhysicians)
    elif modelo == '1':
        valor = omega[3]*(sum(c3[n,d,s].Start for n in Physicians for d in Dates for s in Shifts) + sum(c3prev[n,d,s].Start for n in Physicians for d in PrevShifts for s in Shifts)) + omega[4]*(sum(c4[n,d].Start for n in Physicians for d in Dates) + sum(c4prev[n,d].Start for n in Physicians for d in PrevDays)) + omega[5]*g5.Start + omega[6]*sum(h6[n,d].Start for n in Physicians for d in SaturdayList) + omega[7]*sum(j[7,n].Start for n in Physicians) + omega[8]*sum(j[8,n].Start for n in Physicians) + omega[9]*sum(j[9,n].Start for n in Physicians)   
    return valor

def comprobar_factibilidad(
        lista, modelo, LabDates, Shifts, WeekendDates, t, o, Dates, Locations, x, Physicians, 
        alpha, ForbiddenShiftSuccessions, LastShift, UnavailablePhysicians, l, ForbiddenLocations, 
        beta3, c3, c3prev, PrevShifts, beta, c4, ConsecutiveDays, c4prev, PhysiciansCompleteWeekend, 
        PrevDays, SaturdayList, h6, j, z, UndesiredPhysicians, g5, y):
    
    """
    Comprueba la factibilidad de una solución candidata respecto a todas las restricciones del modelo 1 o 3.

    Args:
        lista (list): subconjunto de médicos a verificar.
        modelo (str): identificador del modelo ('1' o '3').
        ... (otros argumentos son variables del modelo o parámetros del problema)

    Returns:
        (bool, str): `True` y 'Factible' si la solución cumple todas las restricciones.
                     `False` y un código identificador de la restricción violada si no.
    """

    if modelo == '3':
        # H1Constr: máximo 1 turno de trabajo por día
        for n in lista:
            for d in LabDates:
                if sum(t[n,d,s].Start for s in Shifts) != o[n,d].Start:
                    return False, 'H1'

            for d in WeekendDates:
                if (0.5 * (t[n,d,'Early'].Start + t[n,d,'Late'].Start) + t[n,d,'Night'].Start) != o[n,d].Start:
                    return False, 'H1'

        # H2Constr y H3Constr: cobertura mínima y máxima de turnos
        for d in Dates:
            for s in Shifts:
                for k in Locations:
                    cobertura = sum(x[n,d,s,k].Start for n in Physicians)
                    if cobertura < alpha[1,d,s,k]:
                        return False, 'H2'
                    elif cobertura > alpha[2,d,s,k]:
                        return False, 'H3'

        # H5Constr: prohibición de sucesiones de turnos
        for n in lista:
            for d in range(len(Dates) - 1):
                for (s1, s2) in ForbiddenShiftSuccessions:
                    if t[n, Dates[d], s1].Start + t[n, Dates[d+1], s2].Start > 1:
                        return False, 'H5'

        # H5ConstrPrev: prohibiciones con el turno anterior
        for n in lista:
            for (s1, s2) in ForbiddenShiftSuccessions:
                if LastShift[n,s1][0] != 0:
                    if LastShift[n,s1][0] + t[n,'0Mon',s2].Start > 1:
                        return False, 'H5Prev'

        # H6Constr: médicos no disponibles
        for (n, d, s) in UnavailablePhysicians:
            if t[n,d,s].Start > 0:
                return False, 'H6'

        # H7Constr: relación entre localización y actividad
        for n in lista:
            for d in Dates:
                if sum(l[n,d,k].Start for k in Locations) != o[n,d].Start:
                    return False, 'H7'

        # H8Constr: localizaciones prohibidas
        for (n,k) in ForbiddenLocations:
            if l[n,'*',k].Start != 0:
                return False, 'H8'

        # S1Constr: máximo turnos consecutivos
        for n in lista:
            for s in Shifts:
                for d in range(len(Dates) - beta3[n,s]):
                    suma_turnos = sum(t[n,d2,s].Start for d2 in Dates[d:d+beta3[n,s]+1])
                    if suma_turnos - c3[n,Dates[d],s].Start > beta3[n,s]:
                        return False, 'S1'

        # S1ConstrPrev: máximo turnos consecutivos contando histórico
        for n in lista:
            for s in Shifts:
                for d in range(LastShift[n,s][1]):
                    if LastShift[n,s][1] != 0:
                        suma_turnos = LastShift[n,s][1] - d + sum(t[n,d2,s].Start for d2 in Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)])
                        if suma_turnos - c3prev[n, PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]], s].Start > beta3[n,s]:
                            return False, 'S1Prev'

        # S2Constr: máximo días consecutivos de trabajo
        for n in lista:
            for d in range(len(Dates) - beta[4,n]):
                suma_dias = sum(o[n,d2].Start for d2 in Dates[d:d+beta[4,n]+1])
                if suma_dias - c4[n,Dates[d]].Start > beta[4,n]:
                    return False, 'S2'

        # S2ConstrPrev: máximo días consecutivos contando histórico
        for n in lista:
            for d in range(ConsecutiveDays[n]):
                if ConsecutiveDays[n] != 0:
                    suma_dias = ConsecutiveDays[n]-d + sum(o[n,d2].Start for d2 in Dates[0:(beta[4,n]+1-ConsecutiveDays[n]+d)])
                    if suma_dias - c4prev[n, PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]].Start > beta[4,n]:
                        return False, 'S2Prev'

        # S4Constr: fines de semana completos
        for n in PhysiciansCompleteWeekend:
            for d in SaturdayList:
                if (o[n,d].Start + h6[n,d].Start) != (o[n,Dates[Dates.index(d)+1]].Start + h6[n,Dates[Dates.index(d)+1]].Start):
                    return False, 'S4'

        # S5Constr y S6Constr: número mínimo y máximo de turnos
        for n in lista:
            suma_turnos = sum(t[n,d,'Early'].Start + t[n,d,'Late'].Start + 2*t[n,d,'Night'].Start for d in Dates)
            if suma_turnos + j[7,n].Start < beta[7,n]:
                return False, 'S5'
            if suma_turnos - j[8,n].Start > beta[8,n]:
                return False, 'S5'

        # S7Constr: número de fines de semana trabajados
        for n in lista:
            suma_weekends = sum(0.5*(o[n,d].Start + h6[n,d].Start + o[n,Dates[Dates.index(d)+1]].Start + h6[n,Dates[Dates.index(d)+1]].Start) for d in SaturdayList)
            if suma_weekends > beta[9,n] + j[9,n].Start:
                return False, 'S7'

        # Si pasó todos los chequeos
        return True, 'Factible'
    if modelo == '1':
        # H1ConstrMod: relación entre asignaciones y días trabajados (días laborables)
        for n in lista:
            for d in LabDates:
                if sum(x[n,d,s,k].Start for s in Shifts for k in Locations) != o[n,d].Start:
                    return False, 'H1Mod'

        # H4Constr1Mod y H4Constr2Mod: reglas para fines de semana
        for n in lista:
            for d in WeekendDates:
                # H4Constr1Mod: Early turn equivale a z
                if sum(x[n,d,'Early',k].Start for k in Locations) != z[n,d].Start:
                    return False, 'H4_1Mod'
                
                # H4Constr2Mod: Night + z equivale a o
                if (sum(x[n,d,'Night',k].Start for k in Locations) + z[n,d].Start) != o[n,d].Start:
                    return False, 'H4_2Mod'

        # H7Constr: relación entre Early y Late en fines de semana
        for n in lista:
            for d in WeekendDates:
                for k in Locations:
                    if x[n,d,'Early',k].Start != x[n,d,'Late',k].Start:
                        return False, 'H7'

        # H2Constr y H3Constr: cobertura mínima y máxima de turnos
        for d in Dates:
            for s in Shifts:
                for k in Locations:
                    cobertura = sum(x[n,d,s,k].Start for n in Physicians)
                    if cobertura < alpha[1,d,s,k]:
                        return False, 'H2'
                    elif cobertura > alpha[2,d,s,k]:
                        return False, 'H3'

        # H5Constr: prohibición de sucesiones de turnos
        for n in lista:
            for d in range(len(Dates) - 1):
                for (s1, s2) in ForbiddenShiftSuccessions:
                    if sum(x[n,Dates[d],s1,k].Start for k in Locations) + sum(x[n,Dates[d+1],s2,k].Start for k in Locations) > 1:
                        return False, 'H5'

        # H5ConstrPrev: prohibiciones con el turno anterior
        for n in lista:
            for (s1, s2) in ForbiddenShiftSuccessions:
                if LastShift[n,s1][0] != 0:
                    if LastShift[n,s1][0] + sum(x[n,'0Mon',s2,k].Start for k in Locations) > 1:
                        return False, 'H5Prev'

        # H8H6ConstrMod: combinación de ubicaciones prohibidas y médicos no disponibles
        total_prohibido = sum(x[n,d,s,k].Start for d in Dates for s in Shifts for k in Locations if (n,k) in ForbiddenLocations)
        total_no_disponible = sum(x[n,d,s,k].Start for (n,d,s) in UnavailablePhysicians for k in Locations)
        if total_prohibido + total_no_disponible > 0:
            return False, 'H8H6Mod'

        # S1Constr: máximo turnos consecutivos
        for n in lista:
            for s in Shifts:
                for d in range(len(Dates) - beta3[n,s]):
                    suma_turnos = sum(x[n,Dates[d2],s,k].Start for k in Locations for d2 in range(d, d + beta3[n,s] + 1))
                    if suma_turnos - c3[n,Dates[d],s].Start > beta3[n,s]:
                        return False, 'S1'

        # S1ConstrPrev: máximo turnos consecutivos contando histórico
        for n in lista:
            for s in Shifts:
                for d in range(LastShift[n,s][1]):
                    if LastShift[n,s][1] != 0:
                        suma_turnos = LastShift[n,s][1] - d + sum(sum(x[n,d2,s,k].Start for k in Locations) 
                                    for d2 in Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)])
                        if suma_turnos - c3prev[n, PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]], s].Start > beta3[n,s]:
                            return False, 'S1Prev'

        # S2Constr: máximo días consecutivos de trabajo
        for n in lista:
            for d in range(len(Dates) - beta[4,n]):
                suma_dias = sum(o[n,Dates[d2]].Start for d2 in range(d, d + beta[4,n] + 1))
                if suma_dias - c4[n,Dates[d]].Start > beta[4,n]:
                    return False, 'S2'

        # S2ConstrPrev: máximo días consecutivos contando histórico
        for n in lista:
            for d in range(ConsecutiveDays[n]):
                if ConsecutiveDays[n] != 0:
                    suma_dias = ConsecutiveDays[n]-d + sum(o[n,Dates[d2]].Start for d2 in range(0, beta[4,n] + 1 - ConsecutiveDays[n] + d))
                    if suma_dias - c4prev[n, PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]].Start > beta[4,n]:
                        return False, 'S2Prev'

        # S3ConstrMod: asignaciones no deseadas
        total_no_deseado = sum(sum(x[n,d,s,k].Start for k in Locations) for (n,d,s) in UndesiredPhysicians)
        if total_no_deseado != g5.Start:
            return False, 'S3Mod'

        # S4Constr: fines de semana completos
        for n in PhysiciansCompleteWeekend:
            for w in range(len(SaturdayList)):
                d = SaturdayList[w]
                siguiente_dia = Dates[7*(w+1)-1]  # Domingo correspondiente
                if (o[n,d].Start + o[n,siguiente_dia].Start + h6[n,d].Start) != 2 * y[n,d].Start:
                    return False, 'S4'

        # S5Constr y S6Constr: número mínimo y máximo de turnos
        for n in lista:
            suma_turnos = sum(x[n,d,'Early',k].Start for k in Locations for d in Dates) + sum(x[n,d,'Late',k].Start for k in Locations for d in Dates) + 2 * sum(x[n,d,'Night',k].Start for k in Locations for d in Dates)
            if suma_turnos + j[7,n].Start < beta[7,n]:
                return False, 'S5'
            if suma_turnos - j[8,n].Start > beta[8,n]:
                return False, 'S6'
            

        # S7Constr: número de fines de semana trabajados
        for n in lista:
            suma_weekends = sum(y[n,d].Start for d in SaturdayList)
            if suma_weekends - j[9,n].Start > beta[9,n]:
                return False, 'S7'

        # Si pasó todos los chequeos
        return True, 'Factible'