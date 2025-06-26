from gurobipy import *
import os

def modelo0(
        Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, 
        WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, 
        alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend):

    """
    Define y construye el modelo original (modelo 0) de planificación de turnos médicos.

    Parámetros:
        - Todos los conjuntos y parámetros necesarios para la formulación del modelo.

    Retorna:
        - model: Objeto Gurobi con el modelo cargado.
        - Variables de decisión y auxiliares.
        - Restricciones nombradas.
    """


    model = Model(name = "PhysicianModel")

    #VARIABLES

    x = model.addVars(Physicians, Dates, Shifts, Locations, name = 'x', vtype = GRB.BINARY)
    z = model.addVars(Physicians, Dates, name = 'z', vtype = GRB.BINARY)
    o = model.addVars(Physicians, Dates, name = 'o', vtype = GRB.BINARY)
    y = model.addVars(Physicians, SaturdayList, name = 'y', vtype = GRB.BINARY)
    #Modelo extendido:
    #q = model.addVars(Physicians, Locations, name = 'q', vtype = GRB.BINARY)

    #VARIABLES AUXILIARES

    c3 = model.addVars(Physicians, Dates, Shifts, name = 'c3', vtype = GRB.CONTINUOUS)
    c4 = model.addVars(Physicians, Dates, name = 'c4', vtype = GRB.CONTINUOUS)
    c3prev = model.addVars(Physicians, PrevShifts, Shifts, name = 'c3prev', vtype = GRB.CONTINUOUS)
    c4prev = model.addVars(Physicians, PrevDays, name = 'c4prev', vtype = GRB.CONTINUOUS)
    g5 = model.addVars(Physicians, Dates, Shifts, name = 'g5', vtype = GRB.CONTINUOUS)
    h6 = model.addVars(Physicians, SaturdayList, name = 'h6', vtype = GRB.CONTINUOUS)
    j = model.addVars([7, 8, 9], Physicians, name = 'j', vtype = GRB.CONTINUOUS) 
        #añadir , 13, 14, 16, 17, 19 para el modelo extendido
    #Modelo extendido:
    #m15 = model.addVars(Physicians, Locations, name = 'm', vtype = GRB.CONTINUOUS)
    #l18 = model.addVars(Physicians, Weekends, Shifts, name = 'l', vtype = GRB.CONTINUOUS)

    #FUNCIÓN OBJETIVO

    #Costes
    omega = {3: 15, 4: 30, 5: 10, 6: 30, 7: 20, 8: 20, 9: 30}
    
    obj_fun = (
        omega[3]*(c3.sum('*','*','*') + c3prev.sum('*','*','*')) + 
        omega[4]*(c4.sum('*','*') + c4prev.sum('*','*')) + 
        omega[5]*g5.sum('*','*','*') + 
        omega[6]*h6.sum('*','*') + omega[7]*j.sum(7,'*') + 
        omega[8]*j.sum(8,'*') + omega[9]*j.sum(9,'*')
        )

    model.setObjective(obj_fun, GRB.MINIMIZE)


    #RESTRICCIONES
    H1Constr = model.addConstrs((x.sum(n, d, '*', '*') <= 1 for n in Physicians 
                                for d in LabDates), name='H1Constr')
    
    H4Constr1 = model.addConstrs((x.sum(n, d, 'Early', '*') + x.sum(n, d, 'Late', '*')  == 2 * z[n,d] 
                                for n in Physicians for d in WeekendDates), name='H4Constr1')
    
    H4Constr2 = model.addConstrs((x.sum(n, d, 'Night', '*') + z[n,d]  <= 1 for n in Physicians 
                                for d in WeekendDates), name='H4Constr2')
    
    OndConstr = model.addConstrs((x.sum(n, d, '*', '*') <= 2 * o[n,d] for n in Physicians 
                                for d in Dates), name='OndConstr')
    
    H5Constr = model.addConstrs((x.sum(n, Dates[d], s1, '*') + x.sum(n, Dates[d+1], s2, '*')  <= 1 
                                for n in Physicians for d in range(len(Dates[:-1])) 
                                for (s1,s2) in ForbiddenShiftSuccessions), name='H5Constr')
    H5ConstrPrev = model.addConstrs((LastShift[n,s1][0] + x.sum(n, '0Mon', s2, '*')  <= 1 for n in Physicians 
                                    for (s1,s2) in ForbiddenShiftSuccessions if LastShift[n,s1][0] != 0), 
                                    name='H5ConstrPrev')
    
    H8Constr = model.addConstrs((x.sum(n, '*', '*', k)  == 0 for (n,k) in ForbiddenLocations), name='H8Constr')

    H6Constr = model.addConstrs((x.sum(n, d, s, '*')  == 0 for (n,d,s) in UnavailablePhysicians), name='H6Constr')

    H7Constr = model.addConstrs((x[n,d,'Early',k] - x[n,d,'Late',k]  == 0 
                                for n in Physicians for d in WeekendDates for k in Locations), name='H7Constr')

    H2Constr = model.addConstrs((x.sum('*', d, s, k) >= alpha[1,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H2Constr')
    
    H3Constr = model.addConstrs((x.sum('*', d, s, k) <= alpha[2,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H3Constr')
    
    S1Constr = model.addConstrs((x.sum(n, Dates[d:d+beta3[n,s]+1], s, '*') - c3[n,Dates[d],s] <= beta3[n,s] 
                                for n in Physicians for s in Shifts for d in range(len(Dates[:-beta3[n,s]])) ), 
                                name='S1Constr')
    S1ConstrPrev = model.addConstrs((LastShift[n,s][1]-d + 
                                    x.sum(n, Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)], s, '*') 
                                    - c3prev[n,PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]],s] <= beta3[n,s]
                                for n in Physicians for s in Shifts for d in range(LastShift[n,s][1]) 
                                if LastShift[n,s][1] != 0), name='S1ConstrPrev')

    S2Constr = model.addConstrs((o.sum(n, Dates[d:d+beta[4,n]+1]) - c4[n,Dates[d]] <= beta[4,n] 
                                for n in Physicians for d in range(len(Dates[:-beta[4,n]])) ), 
                                name='S2Constr')
    S2ConstrPrev = model.addConstrs((ConsecutiveDays[n]-d + o.sum(n, Dates[0:(beta[4,n]+1-ConsecutiveDays[n]+d)]) 
                                    - c4prev[n,PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]] <= beta[4,n]
                                for n in Physicians for d in range(ConsecutiveDays[n]) 
                                if ConsecutiveDays[n] != 0), name='S2ConstrPrev')

    S3Constr = model.addConstrs((x.sum(n, d, s, '*') <= g5[n,d,s] 
                                for (n,d,s) in UndesiredPhysicians), 
                                name='S3Constr')

    #Complete Weekend
    S4Constr = model.addConstrs((o[n,SaturdayList[w]] + o[n,Dates[7*(w+1)-1]] + h6[n,SaturdayList[w]] 
                                == 2 * y[n,SaturdayList[w]] for n in PhysiciansCompleteWeekend 
                                for w in range(len(SaturdayList))), name='S4Constr')


    #En el artículo se dice que para estas restricciones hay información previa, pero en las instancias no está

    S5Constr = model.addConstrs((x.sum(n,'*',['Early','Late'],'*') + 2 * x.sum(n,'*','Night','*') 
                                + j[7,n] >= beta[7,n] for n in Physicians), name='S5Constr')
    
    S6Constr = model.addConstrs((x.sum(n,'*',['Early','Late'],'*') + 2 * x.sum(n,'*','Night','*') 
                                - j[8,n] <= beta[8,n] for n in Physicians), name='S6Constr')
    
    S7Constr = model.addConstrs((y.sum(n,'*') - j[9,n] <= beta[9,n] for n in Physicians), name='S7Constr')

    #Comentarios sobre el modelo extendido:
    
    #Restricciones para H9, H10, H11, S8 no se pueden definir porque no están los límites en las instancias
    #Restricciones S9 falta conjunto P
    #Se podría definir S10
    #Para definir S11 faltarían los gamma18nws
    #Se podría definir S12


    #Tiempo límite y resolvemos
    return (
        x, z, o, y, model, c3, c4, c3prev, c4prev, g5, h6, j, omega, obj_fun, H1Constr, 
        H4Constr1, H4Constr2, OndConstr, H5Constr, H5ConstrPrev, H8Constr, H6Constr, 
        H7Constr, H2Constr, H3Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, 
        S3Constr, S4Constr, S5Constr, S6Constr, S7Constr)

def modelo1(
        Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, 
        WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, 
        UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, 
        PhysiciansCompleteWeekend):

    """
    Define y construye el modelo modificado (modelo 1) de planificación de turnos médicos.

    Parámetros:
        - Todos los conjuntos y parámetros necesarios para la formulación del modelo.

    Retorna:
        - model: Objeto Gurobi con el modelo cargado.
        - Variables de decisión y auxiliares.
        - Restricciones nombradas.
    """

    model = Model(name = "PhysicianModel")

    #VARIABLES

    x = model.addVars(Physicians, Dates, Shifts, Locations, name = 'x', vtype = GRB.BINARY)
    z = model.addVars(Physicians, Dates, name = 'z', vtype = GRB.BINARY)
    o = model.addVars(Physicians, Dates, name = 'o', vtype = GRB.BINARY)
    y = model.addVars(Physicians, SaturdayList, name = 'y', vtype = GRB.BINARY)


    #VARIABLES AUXILIARES

    c3 = model.addVars(Physicians, Dates, Shifts, name = 'c3', vtype = GRB.CONTINUOUS)
    c4 = model.addVars(Physicians, Dates, name = 'c4', vtype = GRB.CONTINUOUS)
    c3prev = model.addVars(Physicians, PrevShifts, Shifts, name = 'c3prev', vtype = GRB.CONTINUOUS)
    c4prev = model.addVars(Physicians, PrevDays, name = 'c4prev', vtype = GRB.CONTINUOUS)
    g5 = model.addVar(name = 'g5', vtype = GRB.CONTINUOUS)
    h6 = model.addVars(Physicians, SaturdayList, name = 'h6', vtype = GRB.CONTINUOUS)
    j = model.addVars([7, 8, 9], Physicians, name = 'j', vtype = GRB.CONTINUOUS) 

    #FUNCIÓN OBJETIVO

    #Costes
    omega = {3: 15, 4: 30, 5: 10, 6: 30, 7: 20, 8: 20, 9: 30}
    
    obj_fun = (
        omega[3]*(c3.sum('*','*','*') + c3prev.sum('*','*','*')) + 
        omega[4]*(c4.sum('*','*') + c4prev.sum('*','*')) + 
        omega[5]*g5 + omega[6]*h6.sum('*','*') + omega[7]*j.sum(7,'*') + 
        omega[8]*j.sum(8,'*') + omega[9]*j.sum(9,'*'))
    
    model.setObjective(obj_fun, GRB.MINIMIZE)


    #RESTRICCIONES

    H1ConstrMod = model.addConstrs((x.sum(n, d, '*', '*') == o[n,d] for n in Physicians 
                                for d in LabDates), name='H1ConstrMod')                              

    
    H4Constr1Mod = model.addConstrs((x.sum(n, d, 'Early', '*') == z[n,d] 
                                for n in Physicians for d in WeekendDates), name='H4Constr1Mod')
    H4Constr2Mod = model.addConstrs((x.sum(n, d, 'Night', '*') + z[n,d]  == o[n,d] for n in Physicians 
                                for d in WeekendDates), name='H4Constr2Mod')
    
    H5Constr = model.addConstrs((x.sum(n, Dates[d], s1, '*') + x.sum(n, Dates[d+1], s2, '*')  <= 1 
                                for n in Physicians for d in range(len(Dates[:-1])) 
                                for (s1,s2) in ForbiddenShiftSuccessions), name='H5Constr')
    H5ConstrPrev = model.addConstrs((LastShift[n,s1][0] + x.sum(n, '0Mon', s2, '*')  <= 1 for n in Physicians 
                                    for (s1,s2) in ForbiddenShiftSuccessions if LastShift[n,s1][0] != 0), 
                                    name='H5ConstrPrev')
    
    
    H8H6ConstrMod = model.addConstr((sum(x.sum(n, '*', '*', k) for (n,k) in ForbiddenLocations) 
                                    + sum(x.sum(n, d, s, '*') for (n,d,s) in UnavailablePhysicians) == 0), 
                                    name='H8H6ConstrMod')
    
    H7Constr = model.addConstrs((x[n,d,'Early',k] - x[n,d,'Late',k]  == 0 
                                for n in Physicians for d in WeekendDates for k in Locations), name='H7Constr')

    H2Constr = model.addConstrs((x.sum('*', d, s, k) >= alpha[1,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H2Constr')
    
    H3Constr = model.addConstrs((x.sum('*', d, s, k) <= alpha[2,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H3Constr')
    
    S1Constr = model.addConstrs((x.sum(n, Dates[d:d+beta3[n,s]+1], s, '*') - c3[n,Dates[d],s] <= beta3[n,s] 
                                for n in Physicians for s in Shifts for d in range(len(Dates[:-beta3[n,s]])) ), 
                                name='S1Constr')
    S1ConstrPrev = model.addConstrs((LastShift[n,s][1]-d + 
                                    x.sum(n, Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)], s, '*') 
                                    - c3prev[n,PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]],s] <= beta3[n,s]
                                for n in Physicians for s in Shifts for d in range(LastShift[n,s][1]) 
                                if LastShift[n,s][1] != 0), name='S1ConstrPrev')

    S2Constr = model.addConstrs((o.sum(n, Dates[d:d+beta[4,n]+1]) - c4[n,Dates[d]] <= beta[4,n] 
                                for n in Physicians for d in range(len(Dates[:-beta[4,n]])) ), 
                                name='S2Constr')
    S2ConstrPrev = model.addConstrs((ConsecutiveDays[n]-d + o.sum(n, Dates[0:(beta[4,n]+1-ConsecutiveDays[n]+d)]) 
                                    - c4prev[n,PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]] <= beta[4,n]
                                for n in Physicians for d in range(ConsecutiveDays[n]) 
                                if ConsecutiveDays[n] != 0), name='S2ConstrPrev')

    S3ConstrMod = model.addConstr((sum(x.sum(n, d, s, '*') for (n,d,s) in UndesiredPhysicians) == g5), 
                                name='S3ConstrMod') 

    S4Constr = model.addConstrs((o[n,SaturdayList[w]] + o[n,Dates[7*(w+1)-1]] + h6[n,SaturdayList[w]] 
                                == 2 * y[n,SaturdayList[w]] for n in PhysiciansCompleteWeekend 
                                for w in range(len(SaturdayList))), name='S4Constr')


    S5Constr = model.addConstrs((x.sum(n,'*',['Early','Late'],'*') + 2 * x.sum(n,'*','Night','*') 
                                + j[7,n] >= beta[7,n] for n in Physicians), name='S5Constr')
    
    S6Constr = model.addConstrs((x.sum(n,'*',['Early','Late'],'*') + 2 * x.sum(n,'*','Night','*') 
                                - j[8,n] <= beta[8,n] for n in Physicians), name='S6Constr')
    
    S7Constr = model.addConstrs((y.sum(n,'*') - j[9,n] <= beta[9,n] for n in Physicians), name='S7Constr')



    return (x, z, o, y, model, c3, c4, c3prev, c4prev, g5, h6, j, omega, obj_fun, H1ConstrMod, 
            H4Constr1Mod, H4Constr2Mod, H5Constr, H5ConstrPrev, H8H6ConstrMod, H7Constr, H2Constr, 
            H3Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, S3ConstrMod, S4Constr, S5Constr, 
            S6Constr, S7Constr)


def modelo3(Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend):

    """
    Define y construye el modelo reformulado (modelo 3) de planificación de turnos médicos.

    Parámetros:
        - Todos los conjuntos y parámetros necesarios para la formulación del modelo.

    Retorna:
        - model: Objeto Gurobi con el modelo cargado.
        - Variables de decisión y auxiliares.
        - Restricciones nombradas.
    """
    

    model = Model(name = "PhysicianModel")


    #VARIABLES

    x = model.addVars(Physicians, Dates, Shifts, Locations, name = 'x', vtype = GRB.BINARY)
    t = model.addVars(Physicians, Dates, Shifts, name = 't', vtype = GRB.BINARY)
    l = model.addVars(Physicians, Dates, Locations, name = 'l', vtype = GRB.BINARY)
    o = model.addVars(Physicians, Dates, name = 'o', vtype = GRB.BINARY)

    #VARIABLES AUXILIARES

    c3 = model.addVars(Physicians, Dates, Shifts, name = 'c3', vtype = GRB.CONTINUOUS)
    c4 = model.addVars(Physicians, Dates, name = 'c4', vtype = GRB.CONTINUOUS)
    c3prev = model.addVars(Physicians, PrevShifts, Shifts, name = 'c3prev', vtype = GRB.CONTINUOUS)
    c4prev = model.addVars(Physicians, PrevDays, name = 'c4prev', vtype = GRB.CONTINUOUS)
    h6 = model.addVars(Physicians, WeekendDates, name = 'h6', vtype = GRB.CONTINUOUS)
    j = model.addVars([7, 8, 9], Physicians, name = 'j', vtype = GRB.CONTINUOUS) 


    #FUNCIÓN OBJETIVO

    #Costes
    omega = {3: 15, 4: 30, 5: 10, 6: 30, 7: 20, 8: 20, 9: 30}
    
    obj_fun = (
        omega[3]*(c3.sum('*','*','*') + c3prev.sum('*','*','*')) + 
        omega[4]*(c4.sum('*','*') + c4prev.sum('*','*')) + 
        omega[5]*sum(t[n,d,s] for (n,d,s) in UndesiredPhysicians) + omega[6]*h6.sum('*','*') + 
        omega[7]*j.sum(7,'*') + omega[8]*j.sum(8,'*') + omega[9]*j.sum(9,'*'))

    model.setObjective(obj_fun, GRB.MINIMIZE)


    #RESTRICCIONES

    H1Constr = model.addConstrs((t.sum(n, d, '*') == o[n,d] for n in Physicians 
                                for d in LabDates), name='H1Constr')
    
    H1cConstr = model.addConstrs(((1/2)*(t[n,d,'Early'] + t[n,d,'Late']) + t[n,d,'Night'] == o[n,d] for n in Physicians 
                                for d in WeekendDates), name='H1cConstr')
    
    H2Constr = model.addConstrs((x.sum('*', d, s, k) >= alpha[1,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H2Constr')
    
    H3Constr = model.addConstrs((x.sum('*', d, s, k) <= alpha[2,d,s,k] 
                                for d in Dates for s in Shifts for k in Locations), name='H3Constr')
    
    RelConstr1 = model.addConstrs((x[n,d,s,k] <= (1/2)*(t[n,d,s] + l[n,d,k])
                                for n in Physicians for d in Dates for s in Shifts for k in Locations), 
                                name='RelConstr1')

    RelConstr3 = model.addConstrs((x[n,d,s,k] + o[n,d] >= t[n,d,s] + l[n,d,k]
                                for n in Physicians for d in Dates for s in Shifts for k in Locations), 
                                name='RelConstr3')
    
    H5Constr = model.addConstrs((t[n, Dates[d], s1] + t[n, Dates[d+1], s2]  <= 1 
                                for n in Physicians for d in range(len(Dates[:-1])) 
                                for (s1,s2) in ForbiddenShiftSuccessions), name='H5Constr')
    H5ConstrPrev = model.addConstrs((LastShift[n,s1][0] + t[n, '0Mon', s2]  <= 1 for n in Physicians 
                                    for (s1,s2) in ForbiddenShiftSuccessions if LastShift[n,s1][0] != 0), 
                                    name='H5ConstrPrev')
    
    H6Constr = model.addConstrs((t[n, d, s]  == 0 for (n,d,s) in UnavailablePhysicians), name='H6Constr')

    H7Constr = model.addConstrs((l.sum(n,d,'*') == o[n,d] 
                                for n in Physicians for d in Dates), name='H7Constr')
    
    H8Constr = model.addConstrs((l.sum(n,'*', k)  == 0 for (n,k) in ForbiddenLocations), name='H8Constr')
    
    S1Constr = model.addConstrs((t.sum(n, Dates[d:d+beta3[n,s]+1], s) - c3[n,Dates[d],s] <= beta3[n,s] 
                                for n in Physicians for s in Shifts for d in range(len(Dates[:-beta3[n,s]])) ), 
                                name='S1Constr')
    S1ConstrPrev = model.addConstrs((LastShift[n,s][1]-d + 
                                    t.sum(n, Dates[0:(beta3[n,s]+1-LastShift[n,s][1]+d)], s) 
                                    - c3prev[n,PrevShifts[d+len(PrevShifts)-LastShift[n,s][1]],s] <= beta3[n,s]
                                for n in Physicians for s in Shifts for d in range(LastShift[n,s][1]) 
                                if LastShift[n,s][1] != 0), name='S1ConstrPrev')

    S2Constr = model.addConstrs((o.sum(n, Dates[d:d+beta[4,n]+1]) - c4[n,Dates[d]] <= beta[4,n] 
                                for n in Physicians for d in range(len(Dates[:-beta[4,n]])) ), 
                                name='S2Constr')
    S2ConstrPrev = model.addConstrs((ConsecutiveDays[n]-d + o.sum(n, Dates[0:(beta[4,n]+1-ConsecutiveDays[n]+d)]) 
                                    - c4prev[n,PrevDays[d+len(PrevDays)-ConsecutiveDays[n]]] <= beta[4,n]
                                for n in Physicians for d in range(ConsecutiveDays[n]) 
                                if ConsecutiveDays[n] != 0), name='S2ConstrPrev')

    S4Constr = model.addConstrs((o[n,d] + h6[n,d] == o[n,Dates[Dates.index(d)+1]] + h6[n,Dates[Dates.index(d)+1]] 
                                for n in PhysiciansCompleteWeekend 
                                for d in SaturdayList), name='S4Constr')

    S5Constr = model.addConstrs((t.sum(n,'*','Early') + t.sum(n,'*','Late') + 2 * t.sum(n,'*','Night') 
                                + j[7,n] >= beta[7,n] for n in Physicians), name='S5Constr')
    
    S6Constr = model.addConstrs((t.sum(n,'*','Early') + t.sum(n,'*','Late') + 2 * t.sum(n,'*','Night') 
                                - j[8,n] <= beta[8,n] for n in Physicians), name='S6Constr')
    
    S7Constr = model.addConstrs((sum((1/2)*(o[n,d] + h6[n,d] + o[n,Dates[Dates.index(d)+1]] + 
                                            h6[n,Dates[Dates.index(d)+1]]) for d in SaturdayList) 
                                            <= beta[9,n] + j[9,n] for n in Physicians), name='S7Constr')

    return (model, x, t, l, o, c3, c4, c3prev, c4prev, h6, j, omega, obj_fun, 
            H1Constr, H1cConstr, H2Constr, H3Constr, RelConstr1, RelConstr3, H5Constr, H5ConstrPrev, 
            H6Constr, H7Constr, H8Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, S4Constr, 
            S5Constr, S6Constr, S7Constr)
