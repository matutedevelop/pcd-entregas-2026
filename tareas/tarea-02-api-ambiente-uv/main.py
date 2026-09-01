from typing import Any

from datos_viajes import VIAJES

from fastapi import FastAPI
from copy import deepcopy

app = FastAPI(title="API de viajes del curso")


def estimar_duracion(
    distancia_km: float, pasajeros: int, fin_de_semana: bool, **args
) -> float:
    """Estima minutos de viaje con reglas didácticas sencillas."""
    # TODO 1: validar que distancia_km sea positiva.
    if distancia_km < 0:
        raise ValueError("La distancia debe ser positiva")
    # TODO 2: calcular base = 4 minutos por km + 2 minutos fijos.
    duracion = distancia_km * 4 + 2
    # TODO 3: sumar 3 minutos si hay más de 2 pasajeros.
    if pasajeros > 2:
        duracion += 3
    # TODO 4: reducir 10 % si es fin de semana y redondear el resultado
    if fin_de_semana:
        duracion *= 0.9
    # a una cifra decimal antes de devolverlo.
    return round(duracion, 2)


def resumir_viajes(viajes: list[dict]) -> list[dict]:
    """Agrega una duración estimada a cada viaje sin modificar el original."""
    # if viajes is None:
    #     viajes = VIAJES

    viajes_modified = [deepcopy(v) for v in viajes]

    for v in viajes_modified:
        v["duracion_estimada_min"] = estimar_duracion(**v)

    return viajes_modified


@app.get("/")
def home():
    """home endpoint"""
    return {"message": "pending"}


@app.get("/api/v1/viajes")
def viajes_resume() -> dict[str, Any]:
    """log viajes registered"""
    return {f"{v['origen']} - {v['destino']}": v for v in resumir_viajes(VIAJES)}


@app.get("/api/v1/duracion/{distancia_km}")
def duracion(
    distancia_km: float, pasajeros: int = 1, fin_de_semana: bool = False
) -> dict[str, Any]:
    """calculate the estimated duration of a trip based on passed parameters"""
    return {
        "distancia_km": distancia_km,
        "pasajeros": pasajeros,
        "fin_de_semana": fin_de_semana,
        "duracion_estimada": estimar_duracion(distancia_km, pasajeros, fin_de_semana),
    }
