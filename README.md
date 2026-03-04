# Habit Tracker

<br>

Llevaba meses frustrado por no poder encontrar una app que me permita trackear los hábitos de mi día a día de una manera cómoda y que no se me olvide nunca, así que decidí crear un sistema el cual me ayuda a hacerlo.
Mediante un Bot de Telegram el usuario puede ingresar los datos sobre como le fue en el día de una manera sencilla e interactiva, utilizando encuestas o mensajes directos, esos datos son almacenados para luego utilizarlos al finalizar el mes para generar informes que le permitan al usuario visualizar si logró cumplir sus objetivos mensuales y comparar su progreso con meses anteriores.

<br><br> 

Los datos son ingresados por el usuario y almacenados en crudo en una tabla de Postgres, luego son transformados y guardados en otra tabla donde se van a guardar los registros de todos los días. <br> 

Al finalizar el mes, utilizando una tabla aparte que contiene los datos únicamente de ese mes, se genera un informe con un resumen mensual el cual es enviado al usuario a través de email para que pueda tener los resúmenes de cada mes y hacerle su respectivo análisis.

<br><br>

Se decidió guardar los datos en crudo para prevenir posibles cambios en el formato o si ocurre algún error con los datos limpios.

<br>

Utilizamos una tabla auxiliar para los cálculos del cierre de mes para no saturar la tabla principal y ser mas ordenados.

<br>

La duplicación la evitamos gracias a un buen manejo de las consultas SQL, donde en caso de conflicto y dependiendo la situación se actualizan los datos o no pasa nada, pero nunca hay duplicados. Si el DAG falla a mitad de ejecución y se hace un retry, la segunda vez que se ejecute se terminaran de cargar los datos que no fueron cargados antes. 

<br>

Los datos son bien distribuidos entre las tablas para poder diferenciar bien los que corresponden a la capa CORE y capa MART. En la capa CORE tenemos los datos centrales e históricos almacenados de una manera ordenada, en este caso son las tablas habits (tabla dimensión) y habits_logs (tabla FACT). Mientras que en la capa CORE tenemos los datos que van a ser utilizados para generar los informes y ser consumidos por el usuario final, las tablas monthly_progress y monthly_report.

<br>

Monthly_progress tiene el registro acumulado mensual de cada habito mientras que la tabla monthly_report se genera a fin de mes utilizando la tabla monthly_progress para procesar los datos y generar los informes. 


