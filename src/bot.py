import requests
import json
from airflow.models import Variable

token = Variable.get("telegram_token")
    
chat_id = Variable.get("chat_id", default_var=None)

def configurar_teclado_fijo():
    # Armamos la matriz de botones gigantes
    teclado_fijo = {
        "keyboard": [
            [{"text": "🏋️ gym ✅"}, {"text": "🏋️ gym ❌"}],
            [{"text": "📚 leer ✅"}, {"text": "📚 leer ❌"}],
            [{"text": "🗣️ ingles ✅"}, {"text": "🗣️ ingles ❌"}]
        ],
        "resize_keyboard": True, # Hace que los botones se adapten al tamaño de la pantalla
        "is_persistent": True    # Hace que el teclado no desaparezca nunca
    }

    payload = {
        "chat_id": chat_id,
        "text": "🛠️ ¡Teclado Data Engineer configurado!\n\nTocá los botones para registrar tus hábitos.\nPara el sueño, simplemente escribí: 'dormir 7.5'",
        "reply_markup": json.dumps(teclado_fijo)
    }

    respuesta = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
    
    if respuesta.status_code == 200:
        print("¡Teclado configurado! Revisá tu celular.")
    else:
        print("Fallo:", respuesta.text)

configurar_teclado_fijo()