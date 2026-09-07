

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

4. dos ventajas y tres limitaciones de servir modelos mediante pickles locales.

ventajas

- nos permite separar por completo la parte del modelado y entrenamiento de la parte productiva y se integra de forma muy natural en el codigo
- si el modelo esta en memoria o en el disco local del servidor no dependemos del uptime de otro provedor, es decir que nuestra inferencia estara disponible siempre y cuando el servidor tambien lo este

limitaciones

- si no se separa la inferencia del computo del servidor si hay una solicitud de estimacion cuya inferencia sea muy pesada en computo entonces puede realentizar la api

- necesitamos tener en algunos momentos tener mas modelos en disco o memoria de los que planeamos usar. ejemplo: actualizamos el modelo modelo_v1 a modelo_v2, para ello necesitamos cargar ambos modelos a disco o memoria y despues actualizar el endpoint para que apunte a modelo_v2 y solamente despues borrar o bajar modelo_v1, de otra forma tendriamos momentos donde la api no este disponible

- dependencias. Con los pickle hasta donde tengo entendido no se pinnea las dependencias y carga todo el boilerplate de las clases de sklearn entonces digamos por ejemplo actualizamos el python que utiliza nuestro servidor de fastapi a 3.14, y supongamos que esta version es incompatible con algunas cosas de sklearn que utiliza nuestro modelo o con alguna de sus dependencias. Entonces tendriamos errores inesperados e impredecibles.


