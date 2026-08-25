# Definicion de MLOps

MLOps es el conjunto de metodologias, tecnologias y frameworks  para unificar, estandarizar y automatizar las tareas y trabajos de despliegue de modelos de ML en entornos productivos, ademas de tambien abarcar aspectos como la monitorizacion y la evaluacion de los modelos. Todo este conjunto de tecnicas ademas se diseñan inspiradas en filosofias heredadas del DevOps como las metodologias Agile etc.

cuyo fin tambien es facilitar el desarrollo continuo de modelos y el despliegue en productos robustos y concretos de ML. Lo cual es de suma importancia debido a las naturalezas cambiantes de los procesos subyacentes que generan los datos que observamos.

%% MLOps entonces tambien plantea  flujos de trabajo o ci %%


# Sintesis de fuentes


## [Fuente 1 Red hat](https://www.redhat.com/en/topics/ai/what-is-mlops)

la fuente  comienza definiendo MLOps como el conjunto de practicasy workflows inspirdas en DevOps y GitOps para establecer flujos de desarrollo continuo y despliegue para tareas de ML. Directamente despues de eso pasa a nombrar las ventajas de integrar MLOps en los equipos de ML y de datos. Entre las principales estan Reproducibilidad, CICD, mejor governancia, etc. 



## [Fuente 2 Fiddler](https://www.fiddler.ai/blog/mlops-lifecycle)

el documento empieza describiendo las diferentes aplicaciones de ML en el negocio, descriptivo, predictivo y prescriptivo y va de lleno a describir o a plantear lo que para los autores es un modelo o ciclo de MLOps que consiste en resumidas cuentas de lo siguiente

definir el problema -> recoger datos -> tratamiento de datos -> definicion de metricas -> EDA -> entrenamiento de modelo -> deploy del modelo -> release y monitoreo

despues pasa a mencionar ejemplos de productos de ML en los que la adopcion de MLOps es sumamente beneficioso

posteriormente compara MLOps contra su primo mayor DevOps. Donde lo mas destacable es que se añaden las tareas de entrenamiento, observabilidad y back testing de los modelos


# Diferencias

las 2 fuentes tienen temas diferentes como topico principal, no obstante ambos proveen al final del documento  lo que para los respectivos autores consiste el flujo de MLOps. Como es de esperarse, ambos ciclos son relativamente parecidos la unica diferencia es el punto 3 de `automation` de el documento de red hat, que dedica un punto especifico al packaging o contenerizacion del modelo. lo demas resulta similar, aunque evidentemente el documento de red hat es mas introductorio y general


# problemas que resuelve

Lo que yo considero que es de los mayores gains del flujo de MLOps contra el flujo manual arcaico de un Scientist o researcher normal es el hecho de la reproducibilidad y el testing sin estas 2 cosas es mucho mas complicado y riesgoso el deploy de productos de ML confiables y robustos. 

Desde algo tan sencillo como la evaluacion de metricas con una seed local y con los parametros optimizados en un computo local, cuidar ese tipo de cosas es importante para productos robustos y confiables



# Que espero aprender


Siendo concisos lo que me encantaria aprender de MLOps es aquellas partes relacionadas directamente con el desarrollo del modelo, es decir aquellas tareas posteriores a la ingieneria de datos. Me encantaria
aprender de versionado de modelos y todo aquello de control de experimentos

# Enlaces

https://www.redhat.com/en/topics/ai/what-is-mlops

https://www.fiddler.ai/blog/mlops-lifecycle
