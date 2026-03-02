from datetime import datetime

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
