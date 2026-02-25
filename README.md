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

