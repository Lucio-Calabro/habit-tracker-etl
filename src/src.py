
from datetime import datetime
import matplotlib.pyplot as plt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def consultar_respuestas():
    # Funcion que le consulta al bot de telegram si tiene una lista de respuestas pendientes para que sean procesadas

    #Por ahora retorna esto para probar
    return [{
    "update_id": 123456789,
    "message": {
        "message_id": 43,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Lucio"},
        "date": 1772366400,
        "text": "gym 1",
        },
    },
    {
        "update_id": 100000002,
        "callback_query": {
            "id": "4382bfdwjqro23",
            "from": {"id": 987654321, "is_bot": False, "first_name": "Lucio"},
            "message": {
                "message_id": 102,
                "date": 1772452800, # Timestamp: 2 de Marzo de 2026
                "chat": {"id": 987654321, "type": "private"}
            },
            "data": "leer_si" # El formato que espera tu split('_')
        }
    }
]


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
    password = "kjnm utme vmdd bsrv" 
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