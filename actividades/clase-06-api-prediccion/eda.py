import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo

    from pathlib import Path

    import pandas as pd
    import seaborn as sns
    import altair as alt
    from matplotlib import pyplot

    sns.set_theme(style='white',font='VictorMono Nerd Font Mono')

    ARCHIVO_ACTUAL = Path(__file__).resolve()
    RAIZ_REPO = ARCHIVO_ACTUAL.parents[2]
    RUTA_DATOS = RAIZ_REPO / "data/nyc-taxi/green_tripdata_2026-03.parquet"
    viajes = pd.read_parquet(RUTA_DATOS)

    print(viajes.shape)
    print(viajes.columns.tolist())
    print(viajes.head())
    print(viajes.dtypes)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    viajes
    """)
    return


@app.cell
def _():
    viajes.dtypes
    return


@app.cell
def _():
    viajes.isna().sum()
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Tipos de datos

    podemos observar que varios tipos de datos como `payment_type`, o `trip_type` tienen tipos de datos equivocados
    """)
    return


@app.cell
def _():
    minutes = ((viajes['lpep_dropoff_datetime'] - viajes['lpep_pickup_datetime']).dt.total_seconds() // 60)
    sns.histplot(minutes, log_scale=True)
    return (minutes,)


@app.cell
def _(minutes):
    min_lt_60 = minutes.where(minutes < 60)

    # viajes mayores a 60
    print
    print(min_lt_60.isna().sum())

    return


if __name__ == "__main__":
    app.run()
