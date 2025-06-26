import os
import sys
from gurobipy import *
import random
import time
from pathlib import Path


from utils import read_instances, definir_conjuntos 
from modelos import modelo0, modelo1, modelo3
from heuristica import (
    definir_var_ceros, heuristica_ordenada, iniciar_turnos, iniciar_variables, calcular_funcion_objetivo, 
    comprobar_factibilidad
) 

if __name__ == '__main__':
    
 
    # Verificar que se proporcionen exactamente 4 argumentos
    if len(sys.argv) != 5:
        print("Error: Se requieren exactamente 4 argumentos.")
        print("Uso: python script.py <carpeta> <instancia> <tiempo_computacional> <modelo>")
        sys.exit(1)
 
    # Asignar argumentos a variables
    carpeta = sys.argv[1]
    instancia = sys.argv[2]
    tiempo_computacional = sys.argv[3]
    modelo = sys.argv[4]
 
    # Validar si la carpeta existe
    if not os.path.isdir(carpeta):
        print(f"Error: La carpeta '{carpeta}' no existe.")
        sys.exit(1)
 
    # Validar si el archivo de instancia existe dentro de la carpeta
    ruta_instancia = os.path.join(carpeta, instancia)
    if not os.path.isdir(ruta_instancia):
        print(f"Error: La instancia '{instancia}' no se encuentra en la carpeta '{carpeta}'.")
        sys.exit(1)
 
    # Validar si el tiempo computacional es un número válido
    try:
        tiempo_computacional = float(tiempo_computacional)
        if tiempo_computacional <= 0:
            raise ValueError("El tiempo computacional debe ser mayor a 0.")
    except ValueError:
        print("Error: El tiempo computacional debe ser un número válido mayor a 0.")
        sys.exit(1)
 
    # Si todas las validaciones son correctas
    '''print(f"✅ Parámetros recibidos correctamente:")
    print(f"📂 Carpeta: {carpeta}")
    print(f"📄 Instancia: {instancia}")
    print(f"⏳ Tiempo computacional: {tiempo_computacional} segundos")'''

    #Leemos las instancias
    
    folder = Path(f"{carpeta}/{instancia}") 
    #print(folder)

    
    data = read_instances(folder)
    
    #Definimos los conjuntos con definir_conjuntos()
    Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend, Phy_Night_Pre, Night_Consec_Pre, ConsecutiveDays_Heur, Num_Incomp = definir_conjuntos(data)


    Path("Results").mkdir(parents=True, exist_ok=True)
    results_folder = "Results"

    results_file1 = os.path.join(results_folder, f"out_{modelo}_{tiempo_computacional}_{instancia}.txt")
    results_file2 = os.path.join(results_folder, f"out2_{modelo}_{tiempo_computacional}_{instancia}.txt")
    results_file3 = os.path.join(results_folder, f"rel_{modelo}_{instancia}.txt")
    results_file4 = os.path.join(results_folder, f"out_heur_{modelo}_{instancia}.txt")



    #MODELO ORIGINAL
    if modelo == '0':

        x, z, o, y, model, c3, c4, c3prev, c4prev, g5, h6, j, omega, obj_fun, H1Constr, H4Constr1, H4Constr2, OndConstr, H5Constr, H5ConstrPrev, H8Constr, H6Constr, H7Constr, H2Constr, H3Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, S3Constr, S4Constr, S5Constr, S6Constr, S7Constr = modelo0(Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend)
        

    #MODELO REFORMULADO
    elif modelo == '3':

        model, x, t, l, o, c3, c4, c3prev, c4prev, h6, j, omega, obj_fun, H1Constr, H1cConstr, H2Constr, H3Constr, RelConstr1, RelConstr3, H5Constr, H5ConstrPrev, H6Constr, H7Constr, H8Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, S4Constr, S5Constr, S6Constr, S7Constr = modelo3(Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend)

    
    #MODELO MODIFICADO
    elif modelo == '1':

         x, z, o, y, model, c3, c4, c3prev, c4prev, g5, h6, j, omega, obj_fun, H1ConstrMod, H4Constr1Mod, H4Constr2Mod, H5Constr, H5ConstrPrev, H8H6ConstrMod, H7Constr, H2Constr, H3Constr, S1Constr, S1ConstrPrev, S2Constr, S2ConstrPrev, S3ConstrMod, S4Constr, S5Constr, S6Constr, S7Constr = modelo1(Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend)


    with open(results_file1, "w") as f:
        model.setParam("LogFile", results_file1)


    #HEURÍSTICA 
    heuristica = 1
    if heuristica == 1:
        if modelo in ['1','3']:
            ### HEURÍSTICA CON LÍMITE DE TIEMPO (1 MINUTO) ###
            
            start_time = time.time()
            max_time = 60  
            model.update()

            best_fun_obj = float('inf')  # Inicializamos con infinito
            best_Var_Pre = set()  # Mejor solución encontrada
            iterations = 0  # Contador de iteraciones
            solutions_file = f"Results/out_sol_heur_{modelo}_{instancia}.txt"

            #print("Ejecutando heurística por 1 minuto...")

            # Abrimos el archivo en modo escritura (sobrescribirá si existe)
            with open(solutions_file, "w") as sol_file:
            
                while time.time() - start_time < max_time:
                    random.seed(iterations)  # Cambiamos la semilla en cada iteración para diversidad
                    
                    # Reiniciamos variables
                    definir_var_ceros(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, 
                                      SaturdayList, y, c3, c4, c3prev, c4prev, g5, h6, WeekendDates, 
                                      PrevShifts, PrevDays, j, z, model)
                    #si no están definidos z, t, l, etc. definirlos = 0

                    # Generamos nueva solución heurística
                    Var_Pre = heuristica_ordenada(Physicians, Phy_Night_Pre, Night_Consec_Pre, ConsecutiveDays_Heur, Dates, 
                        LabDates, UnavailablePhysicians, Shifts, Locations, alpha, UndesiredPhysicians, 
                        Num_Incomp, SaturdayList)
                    iterations += 1

                    # Iniciamos la solución actual
                    iniciar_turnos(Var_Pre, x, model)
                    iniciar_variables(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, WeekendDates, SaturdayList, y, h6, 
        model, beta3, c3, LastShift, c3prev, PrevShifts, beta, c4, ConsecutiveDays, c4prev, PrevDays, j, 
        UndesiredPhysicians, g5, PhysiciansCompleteWeekend, z)
                    #si no están definidos z, t, l, etc. definirlos = 0
                    
                    # Evaluamos la solución
                    current_fun_obj = calcular_funcion_objetivo(
                        modelo, omega, c3, c3prev, c4, c4prev, Physicians, Dates, Shifts, PrevShifts, 
                        PrevDays, g5, h6, SaturdayList, j, t, UndesiredPhysicians, WeekendDates)
                    #si no están definidos z, t, l, etc. definirlos = 0

                    # Registramos TODAS las soluciones en el archivo
                    sol_file.write(f"{iterations} {int(current_fun_obj)}\n") 
                    
                    # Actualizamos la mejor solución encontrada
                    if current_fun_obj < best_fun_obj:
                        best_Var_Pre = Var_Pre.copy()
                        best_fun_obj = current_fun_obj
                        #print(f"Nueva mejor solución encontrada: {best_fun_obj:.2f} (Iteración {iterations})")

                # Tiempo transcurrido
                elapsed_time = time.time() - start_time
                sol_file.write(f"Tiempo total: {elapsed_time:.2f} segundos")
            # Inicializamos la mejor solución encontrada
            definir_var_ceros(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, 
                                      SaturdayList, y, c3, c4, c3prev, c4prev, g5, h6, WeekendDates, 
                                      PrevShifts, PrevDays, j, z, model)
            iniciar_turnos(best_Var_Pre, x, model)
            iniciar_variables(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, WeekendDates, SaturdayList, y, h6, 
        model, beta3, c3, LastShift, c3prev, PrevShifts, beta, c4, ConsecutiveDays, c4prev, PrevDays, j, 
        UndesiredPhysicians, g5, PhysiciansCompleteWeekend, z)
            final_fun_obj = calcular_funcion_objetivo(
                        modelo, omega, c3, c3prev, c4, c4prev, Physicians, Dates, Shifts, PrevShifts, 
                        PrevDays, g5, h6, SaturdayList, j, t, UndesiredPhysicians, WeekendDates)

            # Comprobación final
            print("\n--- Resultados Finales ---")
            print(f"Tiempo total de ejecución: {elapsed_time:.2f} segundos")
            print(f"Iteraciones completadas: {iterations}")
            print(f"Mejor solución encontrada: {final_fun_obj}")
            
            # Verificación de factibilidad
            fact, restr = comprobar_factibilidad(
                Physicians, modelo, LabDates, Shifts, WeekendDates, t, o, Dates, Locations, x, Physicians, 
                alpha, ForbiddenShiftSuccessions, LastShift, UnavailablePhysicians, l, ForbiddenLocations, 
                beta3, c3, c3prev, PrevShifts, beta, c4, ConsecutiveDays, c4prev, PhysiciansCompleteWeekend, 
                PrevDays, SaturdayList, h6, j, z, UndesiredPhysicians, g5, y)
            print(f"✅ Factibilidad de la solución: {'Factible' if fact else 'No factible'} ({restr})")

            # Guardamos los resultados
            with open(results_file4, "w") as f:
                f.write(f"Nombre Instancia: {instancia} ")
                f.write(f"OFV: {final_fun_obj} ")
                f.write(f"Tiempo: {elapsed_time} ")
            
            print(f"Resumen guardado en: {results_file4}")
            print(f"Todas las soluciones registradas en: {solutions_file}")

            #Queremos iniciar la solución de cero
            primero = 0
            if primero == 1:
                definir_var_ceros(modelo, Physicians, Dates, Shifts, Locations, x, t, l, o, 
                                      SaturdayList, y, c3, c4, c3prev, c4prev, g5, h6, WeekendDates, 
                                      PrevShifts, PrevDays, j, z, model)
                #definir variables 0 de nuevo



    ### OPTIMIZAR Y RESULTADOS ###

    model.setParam('TimeLimit', tiempo_computacional)

    ###     
    #model.setParam("Cutoff", 30000)

    model.optimize()

    #model.write('modelo1.lp')

    if model.status == GRB.OPTIMAL:
        print('Solución óptima encontrada:')
    elif model.status == GRB.TIME_LIMIT:
        print('Tiempo agotado antes de encontrar una solución óptima.')
    elif model.status == GRB.INFEASIBLE:
        print("⚠️ El modelo es infactible. Generando diagnóstico...")
    else:
        print('No se encontró una solución.')   


    print('El valor de la función objetivo es: %f' % model.objval)
    

    with open(results_file2, "w") as f:
        f.write(f"Nombre Instancia: {instancia} ")
        f.write(f"Algoritmo: {modelo} ")
        f.write(f"LB: {model.ObjBound:.2f} ")  # Límite inferior
        f.write(f"UB: {model.objVal:.2f} ")   # Límite superior
        f.write(f"Tiempo: {model.Runtime:.2f} segundos")  # Tiempo de resolución

    print(f"Resumen guardado en: {results_file2}")

    
    

    with open(results_file1, "a") as f:
        model.setParam("LogFile", results_file1)

        for var in model.getVars():
            if var.x != 0:
                f.write(f"{var.varName} = {var.x:.2f}\n")


    print(f"Log y variables guardadas en: {results_file1}")

