#h2 📊 Telegram Habit Tracker & Data Pipeline
Un sistema de seguimiento de hábitos end-to-end que soluciona la fricción de las apps tradicionales mediante el uso de un bot de Telegram, automatizando la ingesta de datos, su procesamiento y la generación de reportes mensuales.

#h2 🚀 El Problema y la Solución
El Problema: Tras meses de frustración probando distintas aplicaciones de habit tracking, noté que el mayor punto de fallo era la fricción al momento de cargar los datos día a día, lo que llevaba al abandono.
La Solución: Desarrollé un flujo de datos automatizado donde el usuario interactúa de manera natural a través de un Bot de Telegram. El sistema ingiere estos mensajes, los procesa y, al finalizar el mes, envía un reporte analítico por email comparando el progreso contra los objetivos mensuales establecidos.

#h2 🏗️ Arquitectura de Datos y Modelado
El proyecto sigue las mejores prácticas de la Ingeniería de Datos, separando la información en capas lógicas para asegurar la escalabilidad y la calidad del dato:

Capa RAW (Crudo): Los mensajes de Telegram se almacenan en su formato original. Esto garantiza la trazabilidad y permite reprocesar la información en caso de errores futuros o cambios en el formato.

Capa CORE (Silver): Los datos estructurados e históricos. Modelados bajo un esquema de estrella (Star Schema):

habits (Dimensión): Almacena el contexto de cada hábito (nombre, unidad de medida, objetivo).

habits_logs (Fact Table): El registro transaccional diario de los hábitos completados.

Capa MART (Gold): Datos listos para el consumo del usuario final y generación de reportes.

monthly_progress: Acumulados mensuales procesados en una tabla auxiliar para no saturar/bloquear la tabla transaccional principal.

monthly_report: Resumen final utilizado para disparar el envío del informe por correo electrónico.

#h2 ⚙️ Decisiones Técnicas Destacadas
Idempotencia y Manejo de Duplicados: Las consultas SQL (Upserts / ON CONFLICT) están diseñadas para que, si el DAG de Airflow falla a mitad de ejecución y requiere un reintento (retry), el sistema procese únicamente los datos faltantes sin generar registros duplicados.

Desacoplamiento Analítico: Se utilizan tablas auxiliares exclusivamente para los cálculos de cierre de mes. Esto mantiene la tabla transaccional (habits_logs) ágil y ordenada.

#h2 🛠️ Stack Tecnológico
Lenguaje: Python

Orquestación: Apache Airflow

Base de Datos: PostgreSQL

Infraestructura: Linux (WSL2)

Integraciones: Telegram API

