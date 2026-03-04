import requests
from airflow.models import Variable
from datetime import datetime
import matplotlib.pyplot as plt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def consultar_respuestas(logger):
    # 1. Traemos el Token que guardaste en Airflow
    # (Si le pusiste otro nombre a la variable, cambialo acá)
    bot_token = Variable.get("telegram_token")
    
    # Traemos el último ID que leímos (el offset). 
    # Si es la primera vez que corre, va a traer None.
    offset = Variable.get("telegram_update_offset", default_var=None)

    # 2. Armamos la URL para tocarle el timbre a Telegram
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    # Le pasamos el offset por parámetro para que no nos repita mensajes
    params = {}
    if offset:
        params["offset"] = offset

    try:
        # 3. Hacemos la llamada a la API
        response = requests.get(url, params=params)
        response.raise_for_status() # Esto tira error si Telegram está caído
        
        data = response.json()

        if not data.get("ok"):
            logger.error(f"Telegram devolvió un error: {data}")
            return []

        resultados = data.get("result", [])

        # 4. Actualizamos el offset para la próxima corrida
        if resultados:
            # Agarramos el update_id del ÚLTIMO mensaje y le sumamos 1
            ultimo_update_id = resultados[-1]["update_id"]
            nuevo_offset = ultimo_update_id + 1
            
            # Guardamos el nuevo offset en Airflow automáticamente
            Variable.set("telegram_update_offset", nuevo_offset)
            logger.info(f"Se bajaron {len(resultados)} mensajes nuevos. Offset actualizado a {nuevo_offset}.")
        else:
            logger.info("El bot no tiene mensajes nuevos.")

        return resultados

    except Exception as e:
        logger.error(f"Error al intentar conectarse con Telegram: {e}")
        return []


def transform_pre_value(pre_value):
    
    si = ['Si','si']
    
    if pre_value in si:
        return 1
    
    else:
        return 0
    
def get_date(habits):
    date = None
    for h in habits:
        payload = h[0]
        
        if 'callback_query' in payload:
            continue

        elif 'message' in payload:
            date =  payload['message']['date']
            date = datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
            return date

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
    remitente = "lucho.calabro@gmail.com" 
    password = Variable.get("email_password")
    destinatario = "lucho.calabro@gmail.com" 

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