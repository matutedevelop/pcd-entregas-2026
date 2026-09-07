import pickle
from pathlib import Path
import time

from preparar_datos import FEATURES, FEATURES_CATEGORICAS, TARGET, preparar_viajes
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

RAIZ = Path(__file__).resolve().parents[2]
train = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-03.parquet")
validacion = preparar_viajes(RAIZ / "data/nyc-taxi/green_tripdata_2026-04.parquet")
preprocesamiento = ColumnTransformer(
    [("zonas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS)],
    remainder="passthrough",
)

rf_regressor = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42,
    verbose=1,
)


modelo = make_pipeline(preprocesamiento, rf_regressor)

begin = time.perf_counter()
modelo.fit(
    train[FEATURES], train[TARGET]
)
end = time.perf_counter()



predicciones = modelo.predict(validacion[FEATURES])
rmse = root_mean_squared_error(validacion[TARGET], predicciones)
artefacto = {
    "modelo": modelo,
    "features": FEATURES,
    "version": "green-taxi-2026-03-rf-zonas-1",
    "rmse_validacion": float(rmse),
}
ruta_modelo = RAIZ / "artifacts/nyc-taxi/modelo-duracion-bosque.pkl"
with ruta_modelo.open("wb") as archivo:
    pickle.dump(artefacto, archivo)

print(f"Entrenamiento: {len(train)} filas")
print(f"Tiempo Entrenamiento: {end - begin} s")
print(f"Validación: {len(validacion)} filas")
print(f"RMSE: {rmse:.2f} minutos")
