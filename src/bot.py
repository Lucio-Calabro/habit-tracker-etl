import requests
import json

TOKEN = '8630998587:AAFnkqf1CE4gEO1l4BimTKFZ47DCPX8dL9g'
CHAT_ID = '8509248214' 

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
        "chat_id": CHAT_ID,
        "text": "🛠️ ¡Teclado Data Engineer configurado!\n\nTocá los botones para registrar tus hábitos.\nPara el sueño, simplemente escribí: 'dormir 7.5'",
        "reply_markup": json.dumps(teclado_fijo)
    }

    respuesta = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload)
    
    if respuesta.status_code == 200:
        print("¡Teclado configurado! Revisá tu celular.")
    else:
        print("Fallo:", respuesta.text)

configurar_teclado_fijo()