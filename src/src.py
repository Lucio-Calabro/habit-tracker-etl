def consultar_respuestas():
    # Funcion que le consulta al bot de telegram si tiene una lista de respuestas pendientes para que sean procesadas

    #Por ahora retorna esto para probar
    return [{
    "update_id": 123456789,
    "message": {
        "message_id": 42,
        "from": {"id": 987654321, "is_bot": False, "first_name": "Lucio"},
        "date": 1708785600,
        "text": "Gym 1",
    },
}]


def transform_pre_value(pre_value):
    
    si = ['Si','si']
    
    if pre_value in si:
        return 1
    
    else:
        return 0