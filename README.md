# Physician Scheduling Problem (PRP)

Este repositorio contiene el código desarrollado para resolver el problema de planificación de turnos médicos, en el contexto del Trabajo Fin de Grado.

## Estructura

- `src/main.py`: Script principal que ejecuta los modelos y la heurística.
- `src/modelos.py`: Contiene las distintas formulaciones matemáticas (modelo 0, 1, 3).
- `src/heuristica.py`: Algoritmo heurístico.
- `src/utils.py`: Funciones auxiliares: lectura de instancias, definición de conjuntos, etc.

## Ejecución

Desde la terminal:

```bash
python src/main.py <carpeta> <instancia> <tiempo> <modelo>
