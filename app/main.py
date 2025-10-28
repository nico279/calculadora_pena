@app.route("/webhook", methods=["GET"])
def verify():
    # Loguear todos los parámetros GET que llegan
    print("=== LLEGADA DE VERIFICACIÓN GET ===")
    for k, v in request.args.items():
        print(f"{k} = {v}")
    print("===================================")

    # Verificación normal
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        print("Token válido, devolviendo challenge")
        return request.args.get("hub.challenge")
    
    print("Token inválido")
    return "Token inválido", 403
