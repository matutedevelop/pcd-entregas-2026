import os
from pathlib import Path
from time import perf_counter
from dotenv import load_dotenv

import mlflow
from mlflow.models import infer_signature
from mlflow import MlflowClient
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
import optuna
from optuna.samplers import GridSampler
from optuna.samplers import TPESampler


load_dotenv(override=True)


FEATURES_NUMERICAS = ["distancia_km", "pasajeros", "hora_recoleccion"]
FEATURES_CATEGORICAS = ["zona_origen", "zona_destino"]
FEATURES = FEATURES_NUMERICAS + FEATURES_CATEGORICAS
TARGET = "duracion_minutos"
DATOS = Path(__file__).parent / "datos"


# Load data related == | == == | == == | == == | ==


def encontrar_raiz() -> Path:
    # Encuentra la raíz del repositorio desde Jupyter o VS Code.
    actual = Path.cwd().resolve()
    for candidata in (actual, *actual.parents):
        if (candidata / "pyproject.toml").exists():
            return candidata
    raise FileNotFoundError("No se encontró la raíz con pyproject.toml")


def cargar_muestra(ruta: Path) -> pd.DataFrame:
    viajes = pd.read_csv(ruta)
    enteras = ["pasajeros", "hora_recoleccion", "zona_origen", "zona_destino"]
    viajes[enteras] = viajes[enteras].astype(int)
    return viajes[FEATURES + [TARGET]]


#  == | == == | == == | == == | ==


# model and tunning related  == | == == | == == | == == | ==


def construir_pipeline(model_name: str) -> Pipeline:
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
        estimador = RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_leaf=5,
            n_jobs=-1,
            random_state=42,
        )
    elif model_name == "gradient_boosting":
        estimador = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=5e-2,
            max_depth=12,
            min_samples_leaf=5,
            random_state=42,
        )
    else:
        raise ValueError(f"Modelo no reconocido: {model_name}")

    return Pipeline([("preprocesamiento", preprocesamiento), ("modelo", estimador)])


def objective_lineal(trial: optuna.trial.Trial) -> float:
    fit_intercept = trial.suggest_categorical("fit_intercept", [True, False])
    pipeline = construir_pipeline("linear_regression")
    pipeline.set_params(modelo__fit_intercept=fit_intercept)

    inicio = perf_counter()
    pipeline.fit(marzo_train[FEATURES], marzo_train[TARGET])
    tiempo = perf_counter() - inicio
    predicciones = pipeline.predict(marzo_tuning[FEATURES])
    rmse = root_mean_squared_error(marzo_tuning[TARGET], predicciones)

    with mlflow.start_run(
        run_name=f"trial-{trial.number:03d}", nested=True
    ) as child_run:
        mlflow.log_param("fit_intercept", fit_intercept)
        mlflow.log_metrics({"tuning_rmse": rmse, "training_time_seconds": tiempo})
        mlflow.set_tags(
            {
                "course": "proyecto-ciencia-datos",
                "term": "otono-2026",
                "homework": "5",
                "role": "tuning-trial",
                "model_family": "linear_regression",
            }
        )
    trial.set_user_attr("run_id", child_run.info.run_id)
    return rmse


def objective_bosque(trial: optuna.trial.Trial) -> float:
    parametros = {
        "max_depth": trial.suggest_int("max_depth", 6, 18, step=2),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 2, 10, step=2),
    }
    pipeline = construir_pipeline("random_forest")
    pipeline.set_params(
        modelo__max_depth=parametros["max_depth"],
        modelo__min_samples_leaf=parametros["min_samples_leaf"],
    )

    inicio = perf_counter()
    pipeline.fit(marzo_train[FEATURES], marzo_train[TARGET])
    tiempo = perf_counter() - inicio
    predicciones = pipeline.predict(marzo_tuning[FEATURES])
    rmse = root_mean_squared_error(marzo_tuning[TARGET], predicciones)

    with mlflow.start_run(
        run_name=f"trial-{trial.number:03d}",
        nested=True,
    ) as child_run:
        mlflow.log_params(parametros)
        mlflow.log_metrics(
            {
                "tuning_rmse": rmse,
                "training_time_seconds": tiempo,
            }
        )
        mlflow.set_tags(
            {
                "course": "proyecto-ciencia-datos",
                "term": "otono-2026",
                "homework": "5",
                "role": "tuning-trial",
                "model_family": "random_forest",
                "trial_number": str(trial.number),
            }
        )
        trial.set_user_attr("run_id", child_run.info.run_id)

    return rmse


def objective_gradient(trial: optuna.trial.Trial) -> float:

    parametros = {
        "n_estimators": trial.suggest_int("n_estimators", 0, 200),
        "learning_rate": trial.suggest_float("learning_rate", 0.001, 1),
        "max_depth": trial.suggest_int("max_depth", 5, 25),
        "min_samples_split": trial.suggest_int("min_samples_split", 10, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 10, 20),
    }
    pipeline = construir_pipeline("gradient_boosting")
    pipeline.set_params(
        modelo__max_depth=parametros["max_depth"],
        modelo__min_samples_leaf=parametros["min_samples_leaf"],
        modelo__n_estimators=parametros["n_estimators"],
        modelo__learning_rate=parametros["learning_rate"],
        modelo__min_samples_split=parametros["min_samples_split"],
    )

    inicio = perf_counter()
    pipeline.fit(marzo_train[FEATURES], marzo_train[TARGET])
    tiempo_final = perf_counter() - inicio
    predicciones = pipeline.predict(marzo_tuning[FEATURES])
    rmse = root_mean_squared_error(marzo_tuning[TARGET], predicciones)

    with mlflow.start_run(
        run_name=f"trial-{trial.number:03d}", nested=True
    ) as child_run:
        mlflow.log_params(parametros)
        mlflow.log_metrics(
            {"tunning_rmse": rmse, "training_time_seconds": tiempo_final}
        )
        mlflow.set_tags(
            {
                "course": "proyecto-ciencia-datos",
                "term": "otono-2026",
                "homework": "5",
                "role": "tuning-trial",
                "model_family": "gradient_boost",
                "trial_number": str(trial.number),
            }
        )

        trial.set_user_attr("run_id", child_run.info.run_id)
        return rmse


def optimize_study(model_name: str, n_trials: int, exhastive: bool = False):

    if model_name not in ("linear_regression", "random_forest", "gradient_boosting"):
        raise ValueError(
            f"{model_name} not an option. Valid options are: [linear_regression, random_forest, gradient_boosting]"
        )
    if exhastive:
        # just applies for linear regression
        sampler = GridSampler({"fit_intercept": [True, False]})
    else:
        sampler = TPESampler(seed=42, n_startup_trials=3)
    study = optuna.create_study(direction="minimize", sampler=sampler)
    run_name = f"tuning-{model_name.replace('_', '-')}"
    objective_fun = OBJECTIVE_FUNS[model_name]

    with mlflow.start_run(run_name=run_name) as parent_run:  # noqa: F841
        mlflow.log_input(dataset_marzo_train, context="training")
        mlflow.log_input(dataset_marzo_tuning, context="tuning-validation")
        mlflow.log_params(
            {
                "optimizer": "optuna-tpe",
                "n_trials": n_trials,
                "sampler_seed": 42,
                "sampler_startup_trials": 3,
                "objective_metric": "tuning_rmse",
            }
        )

        mlflow.set_tags(
            {
                "course": "proyecto-ciencia-datos",
                "term": "otono-2026",
                "homework": "5",
                "role": "tuning-study",
                "model_family": model_name,
            }
        )

        study.optimize(objective_fun, n_trials=n_trials)
        best_optimized_params = dict(study.best_trial.params)
        mlflow.log_params(
            {f"best_{clave}": valor for clave, valor in best_optimized_params.items()}
        )
        mlflow.log_metrics({"best_tuning_rmse": study.best_value})
        mlflow.log_param("best_trial_number", study.best_trial.number)

        model_pipeline = construir_pipeline(model_name)
        model_pipeline.set_params(
            **{f"modelo__{k}": v for k, v in best_optimized_params.items()}
        )

        model_params = model_pipeline.named_steps["modelo"].get_params()

        inicio = perf_counter()
        model_pipeline.fit(marzo[FEATURES], marzo[TARGET])
        tiempo_final = perf_counter() - inicio
        predicciones = model_pipeline.predict(abril[FEATURES])
        rmse_final = root_mean_squared_error(abril[TARGET], predicciones)

        ejemplo = abril[FEATURES].head(5)
        firma = infer_signature(ejemplo, model_pipeline.predict(ejemplo))

        with mlflow.start_run(
            run_name=f"{run_name.replace('_', '-')}-final", nested=True
        ) as final_run:
            mlflow.log_input(dataset_marzo_completo, context="training")
            mlflow.log_input(dataset_abril, context="final-validation")
            mlflow.log_params(model_params)
            mlflow.log_metrics(
                {
                    "validation_rmse": rmse_final,
                    "training_time_seconds": tiempo_final,
                }
            )
            mlflow.set_tags(
                {
                    "course": "proyecto-ciencia-datos",
                    "term": "otono-2026",
                    "homework": "5",
                    "role": "model-final",
                    "model_family": model_name,
                    "best_trial_number": str(study.best_trial.number),
                }
            )
            model = mlflow.sklearn.log_model(
                model_pipeline,
                name="model",
                input_example=ejemplo,
                signature=firma,
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
            )

        return {
            "parent_run_id": parent_run.info.run_id,
            "final_run_id": final_run.info.run_id,
            "model_id": model.model_id,
            "model_family": "random_forest",
            "validation_rmse": rmse_final,
            "training_time_seconds": tiempo_final,
            "best_params": model_params,
        }


# == | == == | == == | == == | ==
# constants == | == == | == == | == == | ==

OBJECTIVE_FUNS = {
    "linear_regression": objective_lineal,
    "random_forest": objective_bosque,
    "gradient_boosting": objective_gradient,
}

if __name__ == "__main__":



    REGISTRY_URI = "databricks-uc"
    CATALOGO = "workspace"
    ESQUEMA = "default"
    MODELO_REGISTRADO = f"{CATALOGO}.{ESQUEMA}.nyc_taxi_trip_duration"
    mlflow.set_registry_uri(REGISTRY_URI)

    if not os.getenv("DATABRICKS_HOST") or not os.getenv("DATABRICKS_TOKEN"):
        raise ValueError("Faltan DATABRICKS_HOST o DATABRICKS_TOKEN en .env")

    TRACKING_URI = "databricks"
    EXPERIMENTO = "/Shared/pcd-otono-2026-tarea-05-nyc-taxi"

    mlflow.set_tracking_uri(TRACKING_URI)
    experimento = mlflow.set_experiment(EXPERIMENTO)

    client = MlflowClient(tracking_uri=TRACKING_URI, registry_uri=REGISTRY_URI)



    marzo = cargar_muestra(DATOS / "green-taxi-train.csv")
    abril = cargar_muestra(DATOS / "green-taxi-validation.csv")

    marzo_train, marzo_tuning = train_test_split(
        marzo,
        test_size=0.2,
        random_state=42,
    )

    # Log data sources
    dataset_marzo_train = mlflow.data.from_pandas(
        marzo_train,
        source="green-taxi-train.csv",
        targets=TARGET,
        name="green-taxi-2026-03-train-interno",
    )
    dataset_marzo_tuning = mlflow.data.from_pandas(
        marzo_tuning,
        source="green-taxi-train.csv",
        targets=TARGET,
        name="green-taxi-2026-03-validacion-tuning",
    )
    dataset_marzo_completo = mlflow.data.from_pandas(
        marzo,
        source="green-taxi-train.csv",
        targets=TARGET,
        name="green-taxi-2026-03-completo",
    )
    dataset_abril = mlflow.data.from_pandas(
        abril,
        source="green-taxi-validation.csv",
        targets=TARGET,
        name="green-taxi-2026-04-final",
    )

    lr_result = optimize_study("linear_regression", 2, exhastive=True)
    rf_result = optimize_study("random_forest", 7)
    gb_result = optimize_study("gradient_boosting", 7)

    model_table = (
        pd.DataFrame(
            [
                lr_result,
                rf_result,
                gb_result,
            ]
        )
        .sort_values("validation_rmse")
        .reset_index(drop=True)
    )

    version_lr = mlflow.register_model(
        model_uri=f"models:/{lr_result['model_id']}",
        name=MODELO_REGISTRADO,
    )
    version_rf = mlflow.register_model(
        model_uri=f"models:/{rf_result['model_id']}",
        name=MODELO_REGISTRADO,
    )
    version_gb = mlflow.register_model(
        model_uri=f"models:/{rf_result['model_id']}",
        name=MODELO_REGISTRADO,
    )

    versiones = {
        "linear_regression": version_lr,
        "random_forest": version_rf,
        "gradient_boosting": version_gb,
    }


    familia_champion = model_table.loc[0, "model_family"]
    familia_challenger = model_table.loc[1, "model_family"]
    familia_candidate = model_table.loc[2, "model_family"]
    version_champion = versiones[familia_champion]
    version_challenger = versiones[familia_challenger]
    version_candidate = versiones[familia_candidate]

    client.set_registered_model_alias(
        name=MODELO_REGISTRADO,
        alias="champion",
        version=version_champion.version,
    )
    client.set_registered_model_alias(
        name=MODELO_REGISTRADO,
        alias="challenger",
        version=version_challenger.version,
    )
    client.set_registered_model_alias(
        name=MODELO_REGISTRADO,
        alias="candidate",
        version=version_candidate.version,
    )

    client.set_model_version_tag(
        MODELO_REGISTRADO,
        version_champion.version,
        "validation_rmse",
        f"{model_table.loc[0, 'validation_rmse']:.6f}",
    )
    client.set_model_version_tag(
        MODELO_REGISTRADO,
        version_challenger.version,
        "validation_rmse",
        f"{model_table.loc[1, 'validation_rmse']:.6f}",
    )
    client.set_model_version_tag(
        MODELO_REGISTRADO,
        version_candidate.version,
        "validation_rmse",
        f"{model_table.loc[1, 'validation_rmse']:.6f}",
    )

    champion_uri = f"models:/{MODELO_REGISTRADO}@champion"
    challenger_uri = f"models:/{MODELO_REGISTRADO}@challenger"
    candidate_uri = f"models:/{MODELO_REGISTRADO}@candidate"

    modelo_champion = mlflow.pyfunc.load_model(champion_uri)
    modelo_challenger = mlflow.pyfunc.load_model(challenger_uri)
    modelo_candidate = mlflow.pyfunc.load_model(candidate_uri)
