import requests
from airflow.models import Variable
#from datetime import datetime
#import matplotlib.pyplot as plt

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
    # # 1. Separamos los datos que vienen de la base de datos
    # # Tu query trae: (month_date, final_value, target_value, compliance_ratio, name)
    # nombres = [fila[4] for fila in monthly_reports]
    # porcentajes = [float(fila[3]) for fila in monthly_reports] # Aseguramos que sea número

    # # 2. Creamos el "lienzo" del gráfico
    # fig, ax = plt.subplots(figsize=(8, 5))

    # # 3. Dibujamos barras horizontales (barh)
    # ax.barh(nombres, porcentajes, color='#4C72B0')

    # # 4. Le ponemos onda y límites (de 0 a 100%)
    # ax.set_xlim(0, 100)
    # ax.set_xlabel('Cumplimiento (%)')
    # ax.set_title('Reporte Mensual de Hábitos')
    # ax.grid(axis='x', linestyle='--', alpha=0.7) # Una grilla sutil de fondo

    # # 5. Le clavamos el numerito exacto al final de cada barra para que se lea fácil
    # for indice, valor in enumerate(porcentajes):
    #     ax.text(valor + 2, indice, f"{valor}%", va='center', fontweight='bold')

    # # 6. Guardamos la imagen en una carpeta temporal
    # # En Linux/Ubuntu, la carpeta /tmp es ideal para archivos de paso que después se borran solos
    # ruta_imagen = '/tmp/reporte_mensual_habitos.png'
    
    # plt.tight_layout() # Ajusta los márgenes para que no se corte ningún texto
    # plt.savefig(ruta_imagen)
    # plt.close() # VITAL en Airflow: cierra el gráfico para no saturar la memoria RAM

    # # Devolvemos la ruta donde quedó guardada la foto para que la agarre tu función send_email()
    # return ruta_imagen

    html_bloques = ""
    
    for fila in monthly_reports:
        nombre = fila[0]
        ytd_ratio = float(fila[1]) if fila[1] else 0.0
        current_ratio = float(fila[2]) if fila[2] else 0.0
        
        # Calculamos la altura de las barras (max 100px)
        altura_ytd = max(int((ytd_ratio / 100) * 100), 1)
        altura_current = max(int((current_ratio / 100) * 100), 1)

        html_bloques += f"""
        <div style="display: inline-block; margin: 15px; text-align: center; font-family: sans-serif;">
            <table cellpadding="0" cellspacing="0" border="0" height="100" style="margin: 0 auto;">
                <tr>
                    <td valign="bottom" style="padding: 0 5px;">
                        <div style="font-size: 10px; color: #555;">{ytd_ratio}%</div>
                        <div style="width: 35px; height: {altura_ytd}px; background-color: #ff8c00; border: 1px solid #333;"></div>
                    </td>
                    <td valign="bottom" style="padding: 0 5px;">
                        <div style="font-size: 10px; color: #555;">{current_ratio}%</div>
                        <div style="width: 35px; height: {altura_current}px; background-color: #4C72B0; border: 1px solid #333;"></div>
                    </td>
                </tr>
            </table>
            <div style="margin-top: 8px; font-weight: bold; font-size: 14px; color: #333;">{nombre.capitalize()}</div>
        </div>
        """

    html_completo = f"""
    <html>
        <body style="background-color: #f9f9f9; padding: 20px;">
            <h2 style="font-family: sans-serif; color: #333; text-align: center;">📊 Tu Reporte Mensual de Hábitos</h2>
            <p style="font-family: sans-serif; color: #666; text-align: center;">
                <span style="color: #ff8c00; font-weight: bold;">Naranja:</span> Promedio Anual | 
                <span style="color: #4C72B0; font-weight: bold;">Azul:</span> Mes Actual
            </p>
            <div style="text-align: center; margin-top: 30px;">
                {html_bloques}
            </div>
        </body>
    </html>
    """
    return html_completo

def send_email(html_content,logger):
    # # 1. Credenciales
    # remitente = Variable.get("email")
    # password = Variable.get("email_password")
    # destinatario = Variable.get("email")

    # # 2. Armamos el "sobre" del correo
    # msg = MIMEMultipart()
    # msg['Subject'] = '🚀 Tu Reporte Mensual de Hábitos'
    # msg['From'] = remitente
    # msg['To'] = destinatario

    # # 3. Le metemos el texto principal
    # cuerpo = "¡Buenas! Acá tenés el resumen de cómo te fue este mes con tus objetivos. ¡A seguir metiéndole!"
    # msg.attach(MIMEText(cuerpo, 'plain'))

    # # 4. Adjuntamos la foto del gráfico
    # try:
    #     with open(ruta_imagen, 'rb') as archivo_imagen:
    #         imagen_adjunta = MIMEImage(archivo_imagen.read(), name="reporte_mensual.png")
    #         msg.attach(imagen_adjunta)
    # except FileNotFoundError:
    #     logger.error(f"No se encontró la imagen en {ruta_imagen}. Se manda el mail sin adjunto.")

    # # 5. Nos conectamos al servidor de Google y disparamos
    # try:
    #     server = smtplib.SMTP('smtp.gmail.com', 587)
    #     server.starttls() # Esto encripta la conexión
    #     server.login(remitente, password)
    #     server.send_message(msg)
    #     server.quit()
    #     logger.info("¡Mail de reporte enviado con éxito!")
    # except Exception as e:
    #     logger.error(f"Explotó el envío de mail: {e}")
    remitente = Variable.get("email")
    password = Variable.get("email_password")
    destinatario = Variable.get("email")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = '🚀 Tu Reporte Mensual de Hábitos'
    msg['From'] = remitente
    msg['To'] = destinatario

    # Adjuntamos el HTML directamente
    parte_html = MIMEText(html_content, 'html')
    msg.attach(parte_html)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()
        logger.info("¡Mail de reporte HTML enviado con éxito!")
    except Exception as e:
        logger.error(f"Explotó el envío de mail: {e}")