import pickle
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MODELO_RF = RAIZ / "artifacts/nyc-taxi/modelo-duracion-bosque.pkl"
RUTA_MODELO_LINEAL = RAIZ / "artifacts/nyc-taxi/modelo-duracion-lineal.pkl"
with RUTA_MODELO_LINEAL.open("rb") as archivo:
    artefacto_lr = pickle.load(archivo)

with RUTA_MODELO_RF.open("rb") as archivo:
    artefacto_rf = pickle.load(archivo)


class SolicitudPrediccion(BaseModel):
    distancia_km: float = Field(gt=0, le=100)
    pasajeros: int = Field(ge=1, le=6)
    hora_recoleccion: int = Field(ge=0, le=23)
    zona_origen: int = Field(ge=1, le=265)
    zona_destino: int = Field(ge=1, le=265)


class RespuestaPrediccion(BaseModel):
    duracion_estimada_minutos: float
    modelo: str
    version_modelo: str


app = FastAPI(title="API de duración de viajes Green Taxi")


@app.post("/predicciones/bosque-aleatorio", response_model=RespuestaPrediccion)
def crear_prediccion_rf(solicitud: SolicitudPrediccion) -> RespuestaPrediccion:
    entrada = pd.DataFrame([solicitud.model_dump()])[artefacto_rf["features"]]
    duracion = float(artefacto_rf["modelo"].predict(entrada)[0])
    return RespuestaPrediccion(
        duracion_estimada_minutos=round(duracion, 1),
        modelo="Random-Forest",
        version_modelo=artefacto_rf["version"],
    )


@app.post("/predicciones/regresion-lineal", response_model=RespuestaPrediccion)
def crear_prediccion_lr(solicitud: SolicitudPrediccion) -> RespuestaPrediccion:
    entrada = pd.DataFrame([solicitud.model_dump()])[artefacto_lr["features"]]
    duracion = float(artefacto_lr["modelo"].predict(entrada)[0])
    return RespuestaPrediccion(
        duracion_estimada_minutos=round(duracion, 1),
        modelo="Regresion-lineal",
        version_modelo=artefacto_lr["version"],
    )
