# import os
# from pathlib import Path
# from time import perf_counter
#
# import mlflow
# import mlflow.pyfunc
# import mlflow.sklearn
# import optuna
# import pandas as pd
# from dotenv import load_dotenv
# from mlflow import MlflowClient
# from mlflow.models import infer_signature
# from optuna.samplers import GridSampler, TPESampler
# from prefect import flow, get_run_logger, task
# from prefect.cache_policies import NO_CACHE
# from sklearn.compose import ColumnTransformer
# from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import root_mean_squared_error
# from sklearn.model_selection import train_test_split
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import OneHotEncoder
#
# load_dotenv(override=True)
#
# FEATURES_NUMERICAS = ["distancia_km", "pasajeros", "hora_recoleccion"]
# FEATURES_CATEGORICAS = ["zona_origen", "zona_destino"]
# FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
# TARGET = "duracion_minutos"
# DATOS = Path(__file__).parent / "datos"
# REGISTRY_URI = "databricks-uc"
# CATALOGO = "workspace"
# ESQUEMA = "default"
# MODELO_REGISTRADO = f"{CATALOGO}.{ESQUEMA}.nyc_taxi_trip_duration"
# TRACKING_URI = "databricks"
# EXPERIMENTO = "/Shared/pcd-otono-2026-tarea-05-nyc-taxi"
#
# MODELOS_VALIDOS = ("linear_regression", "random_forest", "gradient_boosting")
# TAGS_BASE = {
#     "course": "proyecto-ciencia-datos",
#     "term": "otono-2026",
#     "homework": "5",
# }
#
#
# def encontrar_raiz() -> Path:
#
#     actual = Path.cwd().resolve()
#     for candidata in (actual, *actual.parents):
#         if (candidata / "pyproject.toml").exists():
#             return candidata
#     raise FileNotFoundError("No se encontró la raíz con pyproject.toml")
#
#
# @task(name="load_data", retries=5, retry_delay_seconds=3, cache_policy=NO_CACHE)
# def cargar_muestra(ruta: Path) -> pd.DataFrame:
#     viajes = pd.read_csv(ruta)
#     enteras = ["pasajeros", "hora_recoleccion", "zona_origen", "zona_destino"]
#     viajes[enteras] = viajes[enteras].astype(int)
#     return viajes[FEATURES + [TARGET]]
#
#
# def crear_dataset_mlflow(data: pd.DataFrame, *, alias: str, source: str):
#     # Devuelve el Dataset de MLflow para poder usarlo luego en log_input.
#     return mlflow.data.from_pandas(
#         data,
#         source=source,
#         targets=TARGET,
#         name=f"green-taxi-2026-{alias}",
#     )
#
#
#
# def construir_pipeline(model_name: str) -> Pipeline:
#     preprocesamiento = ColumnTransformer(
#         [
#             ("numericas", "passthrough", FEATURES_NUMERICAS),
#             (
#                 "categoricas",
#                 OneHotEncoder(handle_unknown="ignore"),
#                 FEATURES_CATEGORICAS,
#             ),
#         ]
#     )
#
#     if model_name == "linear_regression":
#         estimador = LinearRegression()
#     elif model_name == "random_forest":
#         estimador = RandomForestRegressor(
#             n_estimators=100,
#             max_depth=12,
#             min_samples_leaf=5,
#             n_jobs=-1,
#             random_state=42,
#         )
#     elif model_name == "gradient_boosting":
#         estimador = GradientBoostingRegressor(
#             n_estimators=100,
#             learning_rate=5e-2,
#             max_depth=12,
#             min_samples_leaf=5,
#             random_state=42,
#         )
#     else:
#         raise ValueError(f"Modelo no reconocido: {model_name}")
#
#     return Pipeline([("preprocesamiento", preprocesamiento), ("modelo", estimador)])
#
#
# def evaluar_y_registrar_trial(
#     trial: optuna.trial.Trial,
#     model_name: str,
#     parametros: dict,
#     train: pd.DataFrame,
#     tuning: pd.DataFrame,
# ) -> float:
#     """Entrena con `parametros`, evalúa en tuning y registra un run hijo."""
#     pipeline = construir_pipeline(model_name)
#     pipeline.set_params(**{f"modelo__{k}": v for k, v in parametros.items()})
#
#     inicio = perf_counter()
#     pipeline.fit(train[FEATURES], train[TARGET])
#     tiempo = perf_counter() - inicio
#     predicciones = pipeline.predict(tuning[FEATURES])
#     rmse = root_mean_squared_error(tuning[TARGET], predicciones)
#
#     with mlflow.start_run(
#         run_name=f"trial-{trial.number:03d}", nested=True
#     ) as child_run:
#         mlflow.log_params(parametros)
#         mlflow.log_metrics({"tuning_rmse": rmse, "training_time_seconds": tiempo})
#         mlflow.set_tags(
#             {
#                 **TAGS_BASE,
#                 "role": "tuning-trial",
#                 "model_family": model_name,
#                 "trial_number": str(trial.number),
#             }
#         )
#     trial.set_user_attr("run_id", child_run.info.run_id)
#     return rmse
#
#
# def objective_lineal(trial, train, tuning) -> float:
#     parametros = {
#         "fit_intercept": trial.suggest_categorical("fit_intercept", [True, False]),
#     }
#     return evaluar_y_registrar_trial(
#         trial, "linear_regression", parametros, train, tuning
#     )
#
#
# def objective_bosque(trial, train, tuning) -> float:
#     parametros = {
#         "max_depth": trial.suggest_int("max_depth", 6, 18, step=2),
#         "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 10, step=2),
#     }
#     return evaluar_y_registrar_trial(trial, "random_forest", parametros, train, tuning)
#
#
# def objective_gradient(trial, train, tuning) -> float:
#     parametros = {
#         # n_estimators=0 es inválido en sklearn, por eso el mínimo es 50
#         "n_estimators": trial.suggest_int("n_estimators", 50, 200),
#         "learning_rate": trial.suggest_float("learning_rate", 0.001, 1, log=True),
#         "max_depth": trial.suggest_int("max_depth", 3, 12),
#         "min_samples_split": trial.suggest_int("min_samples_split", 10, 20),
#         "min_samples_leaf": trial.suggest_int("min_samples_leaf", 10, 20),
#     }
#     return evaluar_y_registrar_trial(
#         trial, "gradient_boosting", parametros, train, tuning
#     )
#
#
# OBJECTIVE_FUNS = {
#     "linear_regression": objective_lineal,
#     "random_forest": objective_bosque,
#     "gradient_boosting": objective_gradient,
# }
#
#
# @task(
#     name="optimize-optuna-study",
#     retries=1,  # cada reintento crea runs nuevos en MLflow, por eso solo 1
#     retry_delay_seconds=5,
#     cache_policy=NO_CACHE,
# )
# def optimize_study(
#     model_name: str, n_trials: int, datos: dict, exhaustive: bool = False
# ) -> dict:
#     logger = get_run_logger()
#
#     if model_name not in MODELOS_VALIDOS:
#         raise ValueError(
#             f"{model_name} not an option. Valid options are: {list(MODELOS_VALIDOS)}"
#         )
#
#     marzo_train, marzo_tuning = datos["marzo_train"], datos["marzo_tuning"]
#     marzo, abril = datos["marzo"], datos["abril"]
#
#     if exhaustive:
#         # solo aplica para regresión lineal
#         sampler = GridSampler({"fit_intercept": [True, False]})
#         sampler_name = "optuna-grid"
#     else:
#         sampler = TPESampler(seed=42, n_startup_trials=3)
#         sampler_name = "optuna-tpe"
#
#     study = optuna.create_study(direction="minimize", sampler=sampler)
#     run_name = f"tuning-{model_name.replace('_', '-')}"
#     objective_fun = OBJECTIVE_FUNS[model_name]
#
#     def objective(trial):
#         return objective_fun(trial, marzo_train, marzo_tuning)
#
#     with mlflow.start_run(run_name=run_name) as parent_run:
#         mlflow.log_input(datos["ds_marzo_train"], context="training")
#         mlflow.log_input(datos["ds_marzo_tuning"], context="tuning-validation")
#         mlflow.log_params(
#             {
#                 "optimizer": sampler_name,
#                 "n_trials": n_trials,
#                 "sampler_seed": 42,
#                 "sampler_startup_trials": 3,
#                 "objective_metric": "tuning_rmse",
#             }
#         )
#         mlflow.set_tags(
#             {**TAGS_BASE, "role": "tuning-study", "model_family": model_name}
#         )
#
#         study.optimize(objective, n_trials=n_trials)
#         best_params = dict(study.best_trial.params)
#         logger.info(
#             f"[{model_name}] mejor tuning_rmse={study.best_value:.4f} "
#             f"params={best_params}"
#         )
#
#         mlflow.log_params({f"best_{k}": v for k, v in best_params.items()})
#         mlflow.log_metrics({"best_tuning_rmse": study.best_value})
#         mlflow.log_param("best_trial_number", study.best_trial.number)
#
#         # Reentrenar con los mejores parámetros sobre todo marzo y validar en abril
#         model_pipeline = construir_pipeline(model_name)
#         model_pipeline.set_params(**{f"modelo__{k}": v for k, v in best_params.items()})
#         model_params = model_pipeline.named_steps["modelo"].get_params()
#
#         inicio = perf_counter()
#         model_pipeline.fit(marzo[FEATURES], marzo[TARGET])
#         tiempo_final = perf_counter() - inicio
#         predicciones = model_pipeline.predict(abril[FEATURES])
#         rmse_final = root_mean_squared_error(abril[TARGET], predicciones)
#
#         ejemplo = abril[FEATURES].head(5)
#         firma = infer_signature(ejemplo, model_pipeline.predict(ejemplo))
#
#         with mlflow.start_run(run_name=f"{run_name}-final", nested=True) as final_run:
#             mlflow.log_input(datos["ds_marzo_completo"], context="training")
#             mlflow.log_input(datos["ds_abril"], context="final-validation")
#             mlflow.log_params(model_params)
#             mlflow.log_metrics(
#                 {
#                     "validation_rmse": rmse_final,
#                     "training_time_seconds": tiempo_final,
#                 }
#             )
#             mlflow.set_tags(
#                 {
#                     **TAGS_BASE,
#                     "role": "model-final",
#                     "model_family": model_name,
#                     "best_trial_number": str(study.best_trial.number),
#                 }
#             )
#             model = mlflow.sklearn.log_model(
#                 model_pipeline,
#                 name="model",
#                 input_example=ejemplo,
#                 signature=firma,
#                 serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
#             )
#
#     logger.info(f"[{model_name}] validation_rmse={rmse_final:.4f}")
#
#     return {
#         "parent_run_id": parent_run.info.run_id,
#         "final_run_id": final_run.info.run_id,
#         "model_id": model.model_id,
#         "model_family": model_name,
#         "validation_rmse": rmse_final,
#         "training_time_seconds": tiempo_final,
#         "best_params": best_params,
#     }
#
#
#
# @task(name="register-models", cache_policy=NO_CACHE)
# def registrar_modelos(resultados: dict[str, dict]) -> dict:
#     versiones = {}
#     for familia, resultado in resultados.items():
#         versiones[familia] = mlflow.register_model(
#             model_uri=f"models:/{resultado['model_id']}",
#             name=MODELO_REGISTRADO,
#         )
#     return versiones
#
#
# @task(name="assign-aliases", cache_policy=NO_CACHE)
# def asignar_aliases(resultados: dict[str, dict], versiones: dict) -> pd.DataFrame:
#     logger = get_run_logger()
#     client = MlflowClient(tracking_uri=TRACKING_URI, registry_uri=REGISTRY_URI)
#
#     model_table = (
#         pd.DataFrame(list(resultados.values()))
#         .sort_values("validation_rmse")
#         .reset_index(drop=True)
#     )
#
#     # El mejor es champion, el segundo challenger y el tercero candidate
#     for posicion, alias in enumerate(["champion", "challenger", "candidate"]):
#         familia = model_table.loc[posicion, "model_family"]
#         version = versiones[familia].version
#
#         client.set_registered_model_alias(
#             name=MODELO_REGISTRADO, alias=alias, version=version
#         )
#         client.set_model_version_tag(
#             MODELO_REGISTRADO,
#             version,
#             "validation_rmse",
#             f"{model_table.loc[posicion, 'validation_rmse']:.6f}",
#         )
#         logger.info(f"{alias}: {familia} (versión {version})")
#
#     return model_table
#
#
# @task(name="verify-models", cache_policy=NO_CACHE)
# def verificar_modelos(abril: pd.DataFrame) -> dict:
#     logger = get_run_logger()
#     ejemplo = abril[FEATURES].head(5)
#     predicciones = {}
#
#     for alias in ("champion", "challenger", "candidate"):
#         modelo = mlflow.pyfunc.load_model(f"models:/{MODELO_REGISTRADO}@{alias}")
#         predicciones[alias] = modelo.predict(ejemplo).tolist()
#         logger.info(f"{alias} cargado OK, predicciones: {predicciones[alias]}")
#
#     return predicciones
#
#
#
# def setup_mlflow():
#     if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
#         raise ValueError("Faltan DATABRICKS_HOST o DATABRICKS_TOKEN en .env")
#
#     mlflow.set_registry_uri(REGISTRY_URI)
#     mlflow.set_tracking_uri(TRACKING_URI)
#     mlflow.set_experiment(EXPERIMENTO)
#
#
# @flow(name="train-models", log_prints=True)
# def main():
#     setup_mlflow()
#
#     ruta_train = DATOS / "green-taxi-train.csv"
#     ruta_val = DATOS / "green-taxi-validation.csv"
#
#     marzo = cargar_muestra(ruta_train)
#     abril = cargar_muestra(ruta_val)
#
#     marzo_train, marzo_tuning = train_test_split(
#         marzo, test_size=0.2, random_state=42
#     )
#
#     datos = {
#         "marzo": marzo,
#         "abril": abril,
#         "marzo_train": marzo_train,
#         "marzo_tuning": marzo_tuning,
#         "ds_marzo_train": crear_dataset_mlflow(
#             marzo_train, alias="03-train-interno", source=str(ruta_train)
#         ),
#         "ds_marzo_tuning": crear_dataset_mlflow(
#             marzo_tuning, alias="03-validacion-tuning", source=str(ruta_train)
#         ),
#         "ds_marzo_completo": crear_dataset_mlflow(
#             marzo, alias="03-completo", source=str(ruta_train)
#         ),
#         "ds_abril": crear_dataset_mlflow(
#             abril, alias="04-final", source=str(ruta_val)
#         ),
#     }
#
#     # Secuencial a propósito: MLflow mantiene un run activo por hilo.
#     resultados = {
#         "linear_regression": optimize_study(
#             "linear_regression", 2, datos, exhaustive=True
#         ),
#         "random_forest": optimize_study("random_forest", 7, datos),
#         "gradient_boosting": optimize_study("gradient_boosting", 7, datos),
#     }
#
#     versiones = registrar_modelos(resultados)
#     tabla = asignar_aliases(resultados, versiones)
#     verificar_modelos(abril)
#
#     print(tabla[["model_family", "validation_rmse", "training_time_seconds"]])
#     return tabla
#
#
# if __name__ == "__main__":
#     main()




import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import optuna
import pandas as pd
from dotenv import load_dotenv
from mlflow import MlflowClient
from mlflow.models import infer_signature
from optuna.samplers import GridSampler, TPESampler
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

load_dotenv(override=True)

FEATURES_NUMERICAS = ["distancia_km", "pasajeros", "hora_recoleccion"]
FEATURES_CATEGORICAS = ["zona_origen", "zona_destino"]
FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
TARGET = "duracion_minutos"

RAIZ = Path(__file__).parent
DATOS = RAIZ / "data" / "nyc-taxi"
PARAMS_PATH = RAIZ / "mejores-parametros.json"

YEAR = 2026
MESES = {"marzo": 3, "abril": 4}
URL_BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data"

REGISTRY_URI = "databricks-uc"
CATALOGO = "workspace"
ESQUEMA = "default"
MODELO_REGISTRADO = f"{CATALOGO}.{ESQUEMA}.nyc_taxi_trip_duration"
TRACKING_URI = "databricks"
EXPERIMENTO = "/Shared/pcd-otono-2026-tarea-06-nyc-taxi"

MODELOS_VALIDOS = ("linear_regression", "random_forest", "gradient_boosting")
N_TRIALS = {"linear_regression": 2, "random_forest": 7, "gradient_boosting": 7}
ALIASES = ("champion", "challenger", "candidate")
TAGS_BASE = {
    "course": "proyecto-ciencia-datos",
    "term": "otono-2026",
    "homework": "6",
}

COLUMNAS_CRUDAS = [
    "lpep_pickup_datetime",
    "lpep_dropoff_datetime",
    "PULocationID",
    "DOLocationID",
    "passenger_count",
    "trip_distance",
]
MIN_FILAS = 1_000


class ContratoDatosError(ValueError):
    """Los datos no cumplen el contrato. No se reintenta."""


def nombre_archivo(mes: int) -> str:
    return f"green_tripdata_{YEAR}-{mes:02d}.parquet"


@task(name="ensure-data", retries=3, retry_delay_seconds=5, cache_policy=NO_CACHE)
def asegurar_datos() -> dict[str, Path]:
    """Descarga únicamente los meses que no existen en data/nyc-taxi/."""
    logger = get_run_logger()
    DATOS.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre, mes in MESES.items():
        destino = DATOS / nombre_archivo(mes)
        if destino.exists():
            logger.info(f"{nombre}: ya existe, no se descarga")
        else:
            url = f"{URL_BASE}/{nombre_archivo(mes)}"
            logger.info(f"{nombre}: descargando {url}")
            parcial = destino.with_suffix(".parquet.part")
            with urllib.request.urlopen(url, timeout=60) as resp, open(
                parcial, "wb"
            ) as f:
                while bloque := resp.read(1 << 20):
                    f.write(bloque)
            parcial.replace(destino)  # evita dejar archivos a medias
        rutas[nombre] = destino
    return rutas


def preparar_viajes(ruta: Path, mes: int) -> pd.DataFrame:
    crudo = pd.read_parquet(ruta)
    faltantes = [c for c in COLUMNAS_CRUDAS if c not in crudo.columns]
    if faltantes:
        raise ContratoDatosError(f"{ruta.name}: faltan columnas {faltantes}")

    recoleccion = pd.to_datetime(crudo["lpep_pickup_datetime"])
    entrega = pd.to_datetime(crudo["lpep_dropoff_datetime"])
    viajes = pd.DataFrame(
        {
            "distancia_km": crudo["trip_distance"] * 1.609344,
            "pasajeros": crudo["passenger_count"],
            "hora_recoleccion": recoleccion.dt.hour,
            "zona_origen": crudo["PULocationID"],
            "zona_destino": crudo["DOLocationID"],
            TARGET: (entrega - recoleccion).dt.total_seconds() / 60,
        }
    )

    viajes = viajes[(recoleccion.dt.year == YEAR) & (recoleccion.dt.month == mes)]
    viajes = viajes.dropna()
    viajes = viajes[
        viajes[TARGET].between(1, 120)
        & viajes["distancia_km"].between(0.01, 100)
        & viajes["pasajeros"].between(1, 6)
    ]
    enteras = ["pasajeros", "hora_recoleccion", "zona_origen", "zona_destino"]
    viajes[enteras] = viajes[enteras].astype(int)
    return viajes[FEATURES + [TARGET]].reset_index(drop=True)


def validar_contrato(viajes: pd.DataFrame, nombre: str) -> pd.DataFrame:
    esperadas = FEATURES + [TARGET]
    if list(viajes.columns) != esperadas:
        raise ContratoDatosError(f"{nombre}: columnas {list(viajes.columns)}")
    if len(viajes) < MIN_FILAS:
        raise ContratoDatosError(f"{nombre}: solo {len(viajes)} filas válidas")
    if viajes.isna().any().any():
        raise ContratoDatosError(f"{nombre}: hay valores nulos")

    reglas = {
        "pasajeros": viajes["pasajeros"].between(1, 6),
        "hora_recoleccion": viajes["hora_recoleccion"].between(0, 23),
        "zona_origen": viajes["zona_origen"].between(1, 265),
        "zona_destino": viajes["zona_destino"].between(1, 265),
        "distancia_km": viajes["distancia_km"] > 0,
        TARGET: viajes[TARGET].between(1, 120),
    }
    for columna, ok in reglas.items():
        if not ok.all():
            raise ContratoDatosError(f"{nombre}: valores fuera de rango en {columna}")
    return viajes


@task(name="prepare-and-validate", cache_policy=NO_CACHE)  # sin reintentos
def preparar_datos(ruta: Path, mes: int, nombre: str) -> pd.DataFrame:
    """Misma preparación y contrato para marzo y abril."""
    return validar_contrato(preparar_viajes(ruta, mes), nombre)


def crear_dataset_mlflow(data: pd.DataFrame, *, alias: str, source: str):
    return mlflow.data.from_pandas(
        data, source=source, targets=TARGET, name=f"green-taxi-{YEAR}-{alias}"
    )


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ modelos
def construir_pipeline(model_name: str, parametros: dict | None = None) -> Pipeline:
    preprocesamiento = ColumnTransformer(
        [
            ("numericas", "passthrough", FEATURES_NUMERICAS),
            (
                "categoricas",
                OneHotEncoder(handle_unknown="ignore"),
                FEATURES_CATEGORICAS,
            ),
        ]
    )

    if model_name == "linear_regression":
        estimador = LinearRegression()
    elif model_name == "random_forest":
        estimador = RandomForestRegressor(n_jobs=-1, random_state=42)
    elif model_name == "gradient_boosting":
        estimador = GradientBoostingRegressor(random_state=42)
    else:
        raise ValueError(f"Modelo no reconocido: {model_name}")

    pipeline = Pipeline([("preprocesamiento", preprocesamiento), ("modelo", estimador)])
    if parametros:
        pipeline.set_params(**{f"modelo__{k}": v for k, v in parametros.items()})
    return pipeline


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HPO
# Estas funciones solo reciben marzo: abril no puede entrar al tuning.
def evaluar_y_registrar_trial(trial, model_name, parametros, train, tuning) -> float:
    pipeline = construir_pipeline(model_name, parametros)

    inicio = perf_counter()
    pipeline.fit(train[FEATURES], train[TARGET])
    tiempo = perf_counter() - inicio
    rmse = root_mean_squared_error(tuning[TARGET], pipeline.predict(tuning[FEATURES]))

    with mlflow.start_run(run_name=f"trial-{trial.number:03d}", nested=True):
        mlflow.log_params(parametros)
        mlflow.log_metrics({"tuning_rmse": rmse, "training_time_seconds": tiempo})
        mlflow.set_tags(
            {
                **TAGS_BASE,
                "role": "tuning-trial",
                "model_family": model_name,
                "trial_number": str(trial.number),
            }
        )
    return rmse


def objective_lineal(trial, train, tuning) -> float:
    parametros = {
        "fit_intercept": trial.suggest_categorical("fit_intercept", [True, False]),
    }
    return evaluar_y_registrar_trial(
        trial, "linear_regression", parametros, train, tuning
    )


def objective_bosque(trial, train, tuning) -> float:
    parametros = {
        "n_estimators": 100,
        "max_depth": trial.suggest_int("max_depth", 6, 18, step=2),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 10, step=2),
    }
    return evaluar_y_registrar_trial(trial, "random_forest", parametros, train, tuning)


def objective_gradient(trial, train, tuning) -> float:
    parametros = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 200),
        "learning_rate": trial.suggest_float("learning_rate", 0.001, 1, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "min_samples_split": trial.suggest_int("min_samples_split", 10, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 10, 20),
    }
    return evaluar_y_registrar_trial(
        trial, "gradient_boosting", parametros, train, tuning
    )


OBJECTIVE_FUNS = {
    "linear_regression": objective_lineal,
    "random_forest": objective_bosque,
    "gradient_boosting": objective_gradient,
}


@task(name="optimize-optuna-study", cache_policy=NO_CACHE)
def optimizar_familia(
    model_name: str,
    n_trials: int,
    marzo_train: pd.DataFrame,
    marzo_tuning: pd.DataFrame,
) -> dict:
    logger = get_run_logger()
    if model_name not in MODELOS_VALIDOS:
        raise ValueError(f"{model_name} no es válido: {list(MODELOS_VALIDOS)}")

    if model_name == "linear_regression":
        sampler = GridSampler({"fit_intercept": [True, False]})
        sampler_name = "optuna-grid"
    else:
        sampler = TPESampler(seed=42, n_startup_trials=3)
        sampler_name = "optuna-tpe"

    study = optuna.create_study(direction="minimize", sampler=sampler)
    objective_fun = OBJECTIVE_FUNS[model_name]

    with mlflow.start_run(run_name=f"tuning-{model_name.replace('_', '-')}"):
        mlflow.log_params(
            {"optimizer": sampler_name, "n_trials": n_trials, "sampler_seed": 42}
        )
        mlflow.set_tags(
            {**TAGS_BASE, "role": "tuning-study", "model_family": model_name}
        )
        study.optimize(
            lambda trial: objective_fun(trial, marzo_train, marzo_tuning),
            n_trials=n_trials,
        )
        mlflow.log_metrics({"best_tuning_rmse": study.best_value})

    mejores = dict(study.best_trial.params)
    # Parámetros fijos del objective que no se sugieren (p. ej. n_estimators del RF)
    if model_name == "random_forest":
        mejores = {"n_estimators": 100, **mejores}
    logger.info(f"[{model_name}] tuning_rmse={study.best_value:.4f} params={mejores}")
    return mejores


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ mejores-parametros.json
def guardar_parametros(parametros: dict[str, dict]) -> None:
    contenido = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_trials": N_TRIALS,
        "parametros": parametros,
    }
    PARAMS_PATH.write_text(
        json.dumps(contenido, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def cargar_parametros() -> dict[str, dict]:
    if not PARAMS_PATH.exists():
        raise FileNotFoundError(
            f"No existe {PARAMS_PATH.name}. Ejecuta primero con hacer_tuning=True."
        )
    parametros = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))["parametros"]
    faltantes = [m for m in MODELOS_VALIDOS if m not in parametros]
    if faltantes:
        raise ValueError(f"{PARAMS_PATH.name} no incluye: {faltantes}")
    return parametros


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ entrenamiento final
@task(name="train-final-and-evaluate", cache_policy=NO_CACHE)
def entrenar_final(
    model_name: str,
    parametros: dict,
    marzo: pd.DataFrame,
    abril: pd.DataFrame,
    rutas: dict[str, Path],
) -> dict:
    logger = get_run_logger()
    pipeline = construir_pipeline(model_name, parametros)

    inicio = perf_counter()
    pipeline.fit(marzo[FEATURES], marzo[TARGET])
    tiempo = perf_counter() - inicio
    rmse = root_mean_squared_error(abril[TARGET], pipeline.predict(abril[FEATURES]))

    ejemplo = abril[FEATURES].head(5)
    firma = infer_signature(ejemplo, pipeline.predict(ejemplo))

    with mlflow.start_run(run_name=f"final-{model_name.replace('_', '-')}") as run:
        mlflow.log_input(
            crear_dataset_mlflow(marzo, alias="03-completo", source=str(rutas["marzo"])),
            context="training",
        )
        mlflow.log_input(
            crear_dataset_mlflow(abril, alias="04-final", source=str(rutas["abril"])),
            context="final-validation",
        )
        mlflow.log_params(pipeline.named_steps["modelo"].get_params())
        mlflow.log_metrics({"validation_rmse": rmse, "training_time_seconds": tiempo})
        mlflow.set_tags({**TAGS_BASE, "role": "model-final", "model_family": model_name})
        modelo = mlflow.sklearn.log_model(
            pipeline,
            name="model",
            input_example=ejemplo,
            signature=firma,
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
        )

    logger.info(f"[{model_name}] validation_rmse={rmse:.4f}")
    return {
        "run_id": run.info.run_id,
        "model_id": modelo.model_id,
        "model_family": model_name,
        "validation_rmse": rmse,
        "training_time_seconds": tiempo,
    }


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Registry
@task(name="register-models", cache_policy=NO_CACHE)
def registrar_modelos(resultados: dict[str, dict]) -> dict:
    return {
        familia: mlflow.register_model(
            model_uri=f"models:/{r['model_id']}", name=MODELO_REGISTRADO
        )
        for familia, r in resultados.items()
    }


@task(name="assign-aliases", retries=3, retry_delay_seconds=5, cache_policy=NO_CACHE)
def asignar_aliases(resultados: dict[str, dict], versiones: dict) -> pd.DataFrame:
    logger = get_run_logger()
    client = MlflowClient(tracking_uri=TRACKING_URI, registry_uri=REGISTRY_URI)

    tabla = (
        pd.DataFrame(list(resultados.values()))
        .sort_values("validation_rmse")
        .reset_index(drop=True)
    )
    tabla["alias"] = list(ALIASES)
    for _, fila in tabla.iterrows():
        version = versiones[fila["model_family"]].version
        client.set_registered_model_alias(
            name=MODELO_REGISTRADO, alias=fila["alias"], version=version
        )
        client.set_model_version_tag(
            MODELO_REGISTRADO, version, "validation_rmse", f"{fila['validation_rmse']:.6f}"
        )
        logger.info(f"{fila['alias']}: {fila['model_family']} (versión {version})")
    return tabla


@task(name="verify-models", cache_policy=NO_CACHE)
def verificar_modelos(abril: pd.DataFrame) -> dict:
    logger = get_run_logger()
    ejemplo = abril[FEATURES].head(5)
    predicciones = {}
    for alias in ALIASES:
        modelo = mlflow.pyfunc.load_model(f"models:/{MODELO_REGISTRADO}@{alias}")
        predicciones[alias] = modelo.predict(ejemplo).tolist()
        logger.info(f"{alias} cargado OK: {predicciones[alias]}")
    return predicciones


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ flow
def setup_mlflow():
    if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
        raise ValueError("Faltan DATABRICKS_HOST o DATABRICKS_TOKEN en .env")
    mlflow.set_registry_uri(REGISTRY_URI)
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENTO)


@flow(name="train-models", log_prints=True)
def main(hacer_tuning: bool = True):
    setup_mlflow()

    rutas = asegurar_datos()
    marzo = preparar_datos(rutas["marzo"], MESES["marzo"], "marzo")
    abril = preparar_datos(rutas["abril"], MESES["abril"], "abril")

    if hacer_tuning:
        marzo_train, marzo_tuning = train_test_split(
            marzo, test_size=0.2, random_state=42
        )
        # Secuencial a propósito: MLflow mantiene un run activo por hilo.
        # Aquí solo viaja marzo; abril no se pasa a ninguna task de HPO.
        mejores = {
            familia: optimizar_familia(familia, N_TRIALS[familia], marzo_train, marzo_tuning)
            for familia in MODELOS_VALIDOS
        }
        guardar_parametros(mejores)
    else:
        mejores = cargar_parametros()

    resultados = {
        familia: entrenar_final(familia, mejores[familia], marzo, abril, rutas)
        for familia in MODELOS_VALIDOS
    }

    versiones = registrar_modelos(resultados)
    tabla = asignar_aliases(resultados, versiones)
    verificar_modelos(abril)

    print(tabla[["alias", "model_family", "validation_rmse", "training_time_seconds"]])
    return tabla


if __name__ == "__main__":
    main()

