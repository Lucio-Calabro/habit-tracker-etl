import requests
from airflow.models import Variable
#from datetime import datetime
import matplotlib.pyplot as plt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def consultar_respuestas(logger):
    
    bot_token = Variable.get("telegram_token")
    
    offset = Variable.get("telegram_update_offset", default_var=None)


    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    nuevo_offset = None
    
    params = {}
    if offset:
        params["offset"] = offset

    try:
        response = requests.get(url, params=params)
        response.raise_for_status() 
        
        data = response.json()

        if not data.get("ok"):
            logger.error(f"Telegram devolvió un error: {data}")
            return []

        resultados = data.get("result", [])

        if resultados:
            ultimo_update_id = resultados[-1]["update_id"]
            nuevo_offset = ultimo_update_id + 1
            
            logger.info(f"Se bajaron {len(resultados)} mensajes nuevos. Offset actualizado a {nuevo_offset}.")
        else:
            logger.info("El bot no tiene mensajes nuevos.")

        return resultados, nuevo_offset

    except Exception as e:
        logger.error(f"Error al intentar conectarse con Telegram: {e}")
        return [], None

    
def interpretar_response(response, map_habits):
    habit_id = None
    valor = None

    if "gym" in response:
        habit_id = map_habits['gym']
        valor = 1 if "✅" in response else 0

    elif "leer" in response:
        habit_id = map_habits['leer']
        valor = 1 if "✅" in response else 0

    elif "ingles" in response:
        habit_id = map_habits['ingles']
        valor = 1 if "✅" in response else 0

    elif "dormir" in response:
        habit_id = map_habits['dormir']
        try:
            valor = float(response.split(" ")[1]) 
        except:
            valor = 0 

    return [habit_id,valor]


def generar_reporte(monthly_reports):
    # 1. Separamos los datos que vienen de la base de datos
    # Tu query trae: (month_date, final_value, target_value, compliance_ratio, name)
    nombres = [fila[4] for fila in monthly_reports]
    porcentajes = [float(fila[3]) for fila in monthly_reports] # Aseguramos que sea número

    # 2. Creamos el "lienzo" del gráfico
    fig, ax = plt.subplots(figsize=(8, 5))

    # 3. Dibujamos barras horizontales (barh)
    ax.barh(nombres, porcentajes, color='#4C72B0')

    # 4. Le ponemos onda y límites (de 0 a 100%)
    ax.set_xlim(0, 100)
    ax.set_xlabel('Cumplimiento (%)')
    ax.set_title('Reporte Mensual de Hábitos')
    ax.grid(axis='x', linestyle='--', alpha=0.7) # Una grilla sutil de fondo

    # 5. Le clavamos el numerito exacto al final de cada barra para que se lea fácil
    for indice, valor in enumerate(porcentajes):
        ax.text(valor + 2, indice, f"{valor}%", va='center', fontweight='bold')

    # 6. Guardamos la imagen en una carpeta temporal
    # En Linux/Ubuntu, la carpeta /tmp es ideal para archivos de paso que después se borran solos
    ruta_imagen = '/tmp/reporte_mensual_habitos.png'
    
    plt.tight_layout() # Ajusta los márgenes para que no se corte ningún texto
    plt.savefig(ruta_imagen)
    plt.close() # VITAL en Airflow: cierra el gráfico para no saturar la memoria RAM

    # Devolvemos la ruta donde quedó guardada la foto para que la agarre tu función send_email()
    return ruta_imagen

def send_email(ruta_imagen,logger):
    # 1. Credenciales
    remitente = Variable.get("email")
    password = Variable.get("email_password")
    destinatario = Variable.get("email")

    # 2. Armamos el "sobre" del correo
    msg = MIMEMultipart()
    msg['Subject'] = '🚀 Tu Reporte Mensual de Hábitos'
    msg['From'] = remitente
    msg['To'] = destinatario

    # 3. Le metemos el texto principal
    cuerpo = "¡Buenas! Acá tenés el resumen de cómo te fue este mes con tus objetivos. ¡A seguir metiéndole!"
    msg.attach(MIMEText(cuerpo, 'plain'))

    # 4. Adjuntamos la foto del gráfico
    try:
        with open(ruta_imagen, 'rb') as archivo_imagen:
            imagen_adjunta = MIMEImage(archivo_imagen.read(), name="reporte_mensual.png")
            msg.attach(imagen_adjunta)
    except FileNotFoundError:
        logger.error(f"No se encontró la imagen en {ruta_imagen}. Se manda el mail sin adjunto.")

    # 5. Nos conectamos al servidor de Google y disparamos
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Esto encripta la conexión
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        logger.info("¡Mail de reporte enviado con éxito!")
    except Exception as e:
        logger.error(f"Explotó el envío de mail: {e}")