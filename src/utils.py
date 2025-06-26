import os
from pathlib import Path
import re

def read_history(file_path):
    """Lee el archivo history.txt"""
    with open(file_path, "r") as file:
        lines = file.readlines()
    
    history_data = {}
    start_reading = False

    for line in lines:
        line = line.strip()
        if line == "NURSE_HISTORY":
            start_reading = True
            continue
        if start_reading and line:  # Evita líneas vacías
            parts = line.split()
            history_data[parts[0]] = {
                #"Physician_ID": parts[0],
                "TotalAssignments": parts[1],
                "TotalWorkedWeekends": parts[2],
                "LastShift": parts[3],
                "ConsecutiveAssignmentsLastShift": int(parts[4]),
                "ConsecutiveWorkedDays": int(parts[5]),
                "ConsecutiveDaysOff": int(parts[5])
            }
    
    return history_data


'''Usar para comprobar read_history
from pathlib import Path

history_folder = Path("C:/Users/pablo/Documents/5.2FM/TFGM/InstanciasAnnals/physician_instances/physician/p050_inst_01")
file_name = "history.txt"

ruta_completa = history_folder / file_name 
print(ruta_completa)


data = read_history(ruta_completa)
print(data)
'''


def read_scenario(file_path):
    """Lee el archivo scenario.txt"""
    scenario_data = {
        #"SCENARIO": None,
        "NumberWeeks": None,
        "Locations": [],
        "ShiftTypes": {},
        "ForbiddenShiftSuccessions": [],
        "Contracts": {},
        #"DATE": None,
        "Physicians": {}
    }
    
    with open(file_path, "r") as file:
        lines = file.readlines()
        
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        
        '''if line.startswith("SCENARIO ="):
            scenario_data["SCENARIO"] = line.split("=")[1].strip()'''
        
        if line.startswith("WEEKS ="):
            scenario_data["NumberWeeks"] = int(line.split("=")[1].strip())
        
        elif line.startswith("SKILLS ="):
            num_skills = int(line.split("=")[1].strip())
            scenario_data["Locations"] = [lines[i].strip() for i in range(index + 1, index + 1 + num_skills)]
            index += num_skills
        
        elif line.startswith("SHIFT_TYPES ="):
            num_shifts = int(line.split("=")[1].strip())
            for i in range(index + 1, index + 1 + num_shifts):
                parts = re.split(r"\s*\(|,|\)\s*", lines[i].strip())
                shift_name = parts[0]
                scenario_data["ShiftTypes"][shift_name] = (int(parts[1]), int(parts[2]))
            index += num_shifts
        
        elif line.startswith("FORBIDDEN_SHIFT_TYPES_SUCCESSIONS"):
            index += 1
            while index < len(lines) and lines[index].strip():
                parts = lines[index].strip().split()
                #scenario_data["ForbiddenShiftSuccesions"][parts[0]] = parts[1:]
                if int(parts[1]) > 0:
                    for i in range(2,len(parts)):
                        scenario_data["ForbiddenShiftSuccessions"].append(
                            (parts[0],parts[i])                                         
                        )

                index += 1
        
        elif line.startswith("CONTRACTS ="):
            num_contracts = int(line.split("=")[1].strip())
            for i in range(index + 1, index + 1 + num_contracts):
                parts = re.split(r"\s|\(|,|\)\s*", lines[i].strip())
                for val in parts:
                    if val == "":
                        parts.remove("")
                contract_name = parts[0]
                scenario_data["Contracts"][contract_name] = {
                    "TotalAssignmentsHorizon": (int(parts[1]), int(parts[2])),
                    "ConsecutiveWorkingDays": (int(parts[3]), int(parts[4])),
                    "ConsecutiveDaysOff": (int(parts[5]), int(parts[6])),
                    "MaxWeekends": int(parts[7]),
                    "CompleteWeekendConstraint": int(parts[8])
                }
            index += num_contracts

        #elif line.startswith("DATE ="):
            #scenario_data["DATE"] = int(line.split("=")[1].strip())'''

        elif line.startswith("NURSES ="):
            num_nurses = int(line.split("=")[1].strip())
            for i in range(index + 1, index + 1 + num_nurses):
                parts = lines[i].strip().split()
                nurse_name = parts[0]
                contract_type = parts[1]
                num_skills = int(parts[2])
                skills = parts[3:3 + num_skills]
                scenario_data["Physicians"][nurse_name] = {
                    "contract": contract_type,
                    "number_skills": num_skills,
                    "skills": skills
                }
            index += num_nurses
        
        index += 1
    
    return scenario_data


'''#Usar para comprobar read_scenario
from pathlib import Path

scenario_folder = Path("C:/Users/pablo/Documents/5.2FM/TFGM/InstanciasAnnals/physician_instances/physician/p050_inst_01")
file_name = "scenario.txt"

ruta_completa = scenario_folder / file_name 
print(ruta_completa)


data = read_scenario(ruta_completa)
#print(data)
print("")
#Número de médicos. Algo similar habrá que hacer para definir todos los conjuntos
print(len(data['Physicians']))
Physicians = list(data['Physicians'])
print(Physicians)
'''


def read_week(file_path):
    """
    Lee un archivo weekX.txt y devuelve un diccionario con la siguiente estructura:
      - "REQUIREMENTS": [lista de líneas con los requisitos].
      - "SHIFT_NOT_AVAILABLE_COUNT": (int) Número extraído de la cabecera.
      - "SHIFT_NOT_AVAILABLE": [lista de líneas con la información de turnos no disponibles].
      - "SHIFT_OFF_REQUESTS_COUNT": (int) Número extraído de la cabecera.
      - "SHIFT_OFF_REQUESTS": [lista de líneas con las solicitudes de descanso].
    """
    data = {}
    current_section = None
    
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # Saltar líneas vacías
            
            # Detectar los encabezados de sección
            '''
            if line == "WEEK_DATA":
                current_section = "WEEK_DATA"
                continue
            '''
            if line == "REQUIREMENTS":
                current_section = "Requirements"
                data[current_section] = []
                continue
            elif line.startswith("SHIFT_NOT_AVAILABLE"):
                # Extraer la cantidad (por ejemplo: "SHIFT_NOT_AVAILABLE = 35")
                parts = line.split("=")
                count = int(parts[1].strip()) if len(parts) > 1 else None
                data["UnavailableShiftsNumber"] = count
                current_section = "UnavailableShifts"
                data[current_section] = []
                continue
            elif line.startswith("SHIFT_OFF_REQUESTS"):
                parts = line.split("=")
                count = int(parts[1].strip()) if len(parts) > 1 else None
                data["ShiftOffPreferences"] = count
                current_section = "ShiftOffPreferences"
                data[current_section] = []
                continue
            
            # Procesar contenido según la sección actual
            if current_section is None:
                continue
            elif current_section == "Requirements":
                parts = re.split(r"\s|\(|,|\)\s*", line.strip())
                for val in parts:
                    if val == "":
                        parts.remove("")
                data[current_section].append(parts)
            elif current_section == "UnavailableShifts":
                parts = re.split(r"\s", line.strip())
                for val in parts:
                    if val == "":
                        parts.remove("")
                data[current_section].append(parts)
            elif current_section == "ShiftOffPreferences":
                parts = re.split(r"\s", line.strip())
                '''for val in parts:
                    if val == "":
                        parts.remove("")'''
                data[current_section].append(parts)
            else:
                data[current_section].append(line)
                
    return data


'''#Usar para comprobar read_week
from pathlib import Path

scenario_folder = Path("C:/Users/pablo/Documents/5.2FM/TFGM/InstanciasAnnals/physician_instances/physician/p050_inst_01")
file_name = "week0.txt"

ruta_completa = scenario_folder / file_name 
print(ruta_completa)


data = read_week(ruta_completa)
print(data)
print("")
'''


def read_weeks(folder_path):
    """
    Lee los archivos week0.txt, week1.txt, week2.txt y week3.txt de la carpeta indicada.
    Devuelve un diccionario en el que cada clave es el nombre del archivo y su valor
    es el diccionario devuelto por read_week.
    """
    weeks_data = {}
    for i in range(4):
        file_name = f"week{i}.txt"
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            weeks_data[file_name] = read_week(file_path)
        else:
            print(f"Archivo {file_name} no encontrado en {folder_path}")
    return weeks_data


def read_instances(folder_path):
    """Lee los 6 archivos de una instancia y devuelve los datos organizados"""
    files = {
        "history": "history.txt",
        "scenario": "scenario.txt",
        "weeks": "week0.txt",
    }
    
    data = {}

    # Leer cada archivo según corresponda
    for key, filename in files.items():
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            if key == "history":
                data[key] = read_history(file_path)
            elif key == "scenario":
                data[key] = read_scenario(file_path)
            else:  # weeks
                data[key] = read_weeks(folder_path)
        else:
            print(f"⚠️ Advertencia: {filename} no encontrado en {folder_path}")

    return data


def definir_conjuntos(data):

    """
        Se definen los conjuntos y parámetros característicos de cada instancia

        Input: conjunto data generado a partir de las instancias

        Output: conjuntos y parámetros
    """

    #Definimos el conjunto de médicos: N
    Physicians = list(data["scenario"]['Physicians'])
    '''print('Physicians:')
    print(Physicians)
    print("")
    '''
    #Definimos el conjunto de médicos para los que aplica la restricción de 'complete weekend'
    PhysiciansCompleteWeekend = []
    for n in Physicians:
        contract_type = data['scenario']['Physicians'][n]['contract']
        '''print(n)
        print(data['scenario']['Physicians'][n]['contract'])
        print(data['scenario']['Contracts'][contract_type]['CompleteWeekendConstraint'])'''
        if data['scenario']['Contracts'][contract_type]['CompleteWeekendConstraint'] == 1:
            PhysiciansCompleteWeekend.append(n)

    '''print(PhysiciansCompleteWeekend)
    print(PhysiciansCompleteWeekend == Physicians)'''

    #Definimos el conjunto de días: D, y el conjunto de fines de semana: tilde(W). 
    # Definimos también tilde(D) y D\tilde(D)
    Dates = []
    LabDates = []
    WeekendDates = []
    Weekends = []
    NWeeks = data["scenario"]["NumberWeeks"]
    Week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for w in range(NWeeks):
        Weekends.append(w)
        for d in Week:
            Dates.append(f"{w}{d}")
            if ((d != 'Sat') & (d != 'Sun')):
                LabDates.append(f"{w}{d}")
            else:
                WeekendDates.append(f"{w}{d}")
    #Conjunto de sábados: W
    SaturdayList = []
    for w in Weekends:
        SaturdayList.append(f'{w}Sat')
    '''print('Dates:')
    print(Dates)
    print(Weekends)
    print(WeekendDates)
    print(SaturdayList)
    print("")'''

    '''print('Comprobación días:')
    print(len(LabDates + WeekendDates))'''

    #Definimos el conjunto de turnos: S
    Shifts = list(data["scenario"]["ShiftTypes"])

    '''print('Shifts:')
    print(Shifts)
    print("")'''

    #Definimos el conjunto de localizaciones: K
    Locations = list(data["scenario"]["Locations"])
    NumberLocations = len(Locations)

    '''print('Locations:')
    print(Locations)
    print("")'''

    #Definimos el conjunto de sucesiones inválidas de turnos: hat(S)
    ForbiddenShiftSuccessions = data['scenario']['ForbiddenShiftSuccessions']
    '''print('Sucesiones inválidas de turnos:')
    print(ForbiddenShiftSuccessions)'''

    #Definimos el conjunto de localizaciones no permitidas: L
    ForbiddenLocations = []
    #print(data["scenario"]['Physicians'])
    for n in data["scenario"]['Physicians']:
        if data["scenario"]['Physicians'][n]['number_skills'] < NumberLocations:
            for k in Locations:
                if k not in data["scenario"]['Physicians'][n]['skills']:
                    ForbiddenLocations.append((n,k))

    '''print('Localizaciones no permitidas:')
    print(ForbiddenLocations)'''

    #Definimos el conjunto de turnos/días no disponibles: R
    UnavailablePhysicians = []
    Num_Incomp = {} #número de incompatibilidades de cada médico
    for n in Physicians:
        Num_Incomp[n] = 0

    for i in range(0,NWeeks):
        for line in data['weeks'][f'week{i}.txt']['UnavailableShifts']:
            if line[1] == 'Any':
                for s in Shifts:
                    UnavailablePhysicians.append((line[0],f'{i}'+line[2],s))
            else:
                UnavailablePhysicians.append((line[0],f'{i}'+line[2],line[1]))

    '''print('R:')
    print(UnavailablePhysicians)
    print('')'''

    #Definimos el conjunto de turnos/días no deseados: U
    UndesiredPhysicians = []
    for i in range(0,NWeeks):
        for line in data['weeks'][f'week{i}.txt']['ShiftOffPreferences']:
            if line[1] == 'Any':
                for s in Shifts:
                    UndesiredPhysicians.append((line[0],f'{i}'+line[2],s))
            else:
                UndesiredPhysicians.append((line[0],f'{i}'+line[2],line[1]))

    '''print('U:')
    print(UndesiredPhysicians)'''

    #El conjunto de preferencias de localizaciones (P) no está en las instancias


    #CONSTANTES DEL PROBLEMA

    #Definimos los vectores con los requisitos de demanda mínima y máxima
    alpha={}
    for w in range(NWeeks):

        for line in data['weeks'][f'week{w}.txt']['Requirements']:
            for d in range(7):
                alpha[1,Dates[w*7+d],line[0],line[1]] = int(line[2*d+2])
                alpha[2,Dates[w*7+d],line[0],line[1]] = int(line[2*d+3])
                '''Min[Dates[w*7+d],line[0],line[1]] = int(line[2*d+2])
                Max[Dates[w*7+d],line[0],line[1]] = int(line[2*d+3])'''


    '''print(alpha)
    print(alpha[1,'2Sun','Night','InPatientUnit1'])'''
    

    # Definimos los números máximos para turnos consecutivos
    beta3 = {} #el modelo sólo lo hace para Night, pero vamos a escribirlo para cada turno, porque lo dan las instancias
    for n in Physicians:
        for s in Shifts:
            beta3[n,s] = data['scenario']['ShiftTypes'][s][1]
    
    '''print('beta3:')
    print(beta3)'''

    beta = {} #para el resto de superíndices
    for n in Physicians:
        contract_type = data['scenario']['Physicians'][n]['contract']
        beta[4,n] = data['scenario']['Contracts'][contract_type]['ConsecutiveWorkingDays'][1]
        beta[7,n] = data['scenario']['Contracts'][contract_type]['TotalAssignmentsHorizon'][0]
        beta[8,n] = data['scenario']['Contracts'][contract_type]['TotalAssignmentsHorizon'][1]
        beta[9,n] = data['scenario']['Contracts'][contract_type]['MaxWeekends']
        #beta10, 11, 12 y 13 no están proporcionados ni por el artículo ni por las instancias

    #print(beta)

    #Guardamos la información del turno de los días previos
    LastShift = {}
    PrevShifts = []
    ConsecutiveDays = {} 
    PrevDays = []
    ConsecutiveDays_Heur={} #igual que el anterior, pero necesitamos definirlo de otra manera

    #*No consideramos las secuencias de días o turnos consecutivas que están al completo en el mes previo
    for n in Physicians:
        ConsecutiveDays[n] = min(data["history"][n]['ConsecutiveWorkedDays'],beta[4,n]) #*
        ConsecutiveDays_Heur[n] = data["history"][n]['ConsecutiveWorkedDays']
        if data["history"][n]['ConsecutiveWorkedDays'] > len(PrevDays):
            PrevDays = []
            for l in range(data["history"][n]['ConsecutiveWorkedDays'],0,-1):
                PrevDays.append(str(-l))
        for s in Shifts:
            if data["history"][n]['LastShift'] == s:
                LastShift[n,s] = (1,min(data["history"][n]['ConsecutiveAssignmentsLastShift'],beta3[n,s])) #*
                if LastShift[n,s][1] > len(PrevShifts):
                    PrevShifts = []
                    for l in range(LastShift[n,s][1],0,-1):
                        PrevShifts.append(str(-l))
            else:
                LastShift[n,s] = (0,0)


    #necesitamos una lista de médicos que trabajaron en el turno anterior de Noche

    Phy_Night_Pre = []
    Night_Consec_Pre = {}
    for n in Physicians:
        if LastShift[n,'Night'][0] == 1:
            Phy_Night_Pre.append(n)
            Night_Consec_Pre[n] = LastShift[n,'Night'][1]
        if LastShift[n,'Night'][0] == 0:
            Night_Consec_Pre[n] = 0
    
    '''print('')
    print("-1:")
    print(LastShift)
    print(PrevShifts)
    print(ConsecutiveDays)
    print(PrevDays)'''


    return (Physicians, Dates, Shifts, Locations, SaturdayList, PrevDays, PrevShifts, LabDates, 
            WeekendDates, ForbiddenShiftSuccessions, LastShift, ForbiddenLocations, UnavailablePhysicians, 
            alpha, beta3, beta, ConsecutiveDays, UndesiredPhysicians, PhysiciansCompleteWeekend, 
            Phy_Night_Pre, Night_Consec_Pre, ConsecutiveDays_Heur, Num_Incomp)

