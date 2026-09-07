

# Resultados de entrenamiento


|  modelo   |   RMSE Abril (Test score)  | tiempo de entrenamiento    | tamaño artifact|
| --- | --- | --- | --- |
| Regresion lineal    | 5.11 min     | 0.256018 s | 0.0085 mb     |
| Random Forest | 4.52 | 1.7309 s |11.3 mb |

1. cuál modelo obtuvo el menor RMSE y qué significa esa diferencia en minutos

el mejor modelo fue el Random Forest con un RMSE de 4.52 min vs 5.11 de la regresion lineal, esto indica que en promedio los errores del random forest son 0.59 min menores a los de la regresion lineal

2. cuál requirió más tiempo y produjo el artefacto más grande

El random Forest requirio casi 7 veces  el tiempo de entrenamiento que la regresion lineal, y el pickle es tambien de de casi 4 ordenes de magnitud mas grande que el de la regresion lineal

3. cuál elegirías para este ejercicio y qué criterio sostiene tu decisión

con el supuesto que la prediccion esta hecho para ser visualizada en una aplicacion tipo uber o didi, eligiria la regresion lineal, en efecto aplicando un redondeo a minutos enteros ambos modelos promedian el mismo error. Si por otra parte mi modelo fuera a ser para pricing o alguna area de negocio de analitica se pudiera llegar a aprovechar el error marginalmente menor, no obstante para la basta mayoria de los casos es mas recomendable la regresion lineal

