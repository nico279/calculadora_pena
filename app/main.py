# main.py (SOLO CAMBIAR ESTE BLOQUE)

from flask import Flask, request
import requests
import json
import os
# ... (otras importaciones)

app = Flask(__name__)


# ...

# --- CREDENCIALES LEÍDAS DEL ENTORNO DE RENDER ---
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "27148101")
# Usa el nuevo token como default si no lo definimos en Render
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "EAATPgVJeq5oBPgE15WNBZCCc4ztxe21UgIiac2rDSyoUlFUiztDuhXoEZAFCZBNe0wo2EpgaLOdjXZBmshZCJ2yHsJrXdFDKGM2XmEIzydRz7SDvquqDuHocVwyEyZATsuju4ibHMvS8T0Xhnfd9WZAmSu2Ff9mFnvGBDVWD7AEg7n2ojq9ijs1lCWaRd9x6RzZAEQZDZD")
ID_NUMERO_TELEFONO = os.environ.get("ID_NUMERO_TELEFONO", "868674859654579")
# ...
# ... (El resto del script de la calculadora sigue igual)
# --- ESTRUCTURA DE LA CALCULADORA ---
# Estructura temporal (en memoria) para almacenar datos de cada usuario
# La clave es el número de teléfono del usuario.
usuarios = {}


# 1️⃣ Verificación del Webhook (GET)
@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Token inválido", 403


# 2️⃣ Recibir y Procesar Mensajes (POST)
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    
    # Intenta obtener el mensaje del formato de Meta
    try:
        # Extraer el número de teléfono del remitente
        phone_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        
        # Extraer el texto del mensaje (maneja el caso de que no sea un mensaje de texto)
        message_object = data["entry"][0]["changes"][0]["value"]["messages"][0]
        text = message_object.get("text", {}).get("body", "")
        
        # --- LÓGICA DE LA CALCULADORA ---
        procesar_mensaje_calculadora(phone_number, text.strip().lower())

    except Exception as e:
        # Esto captura errores si el mensaje no es de texto (ej: sticker, imagen)
        # o si la estructura del JSON es inesperada.
        print(f"Error al procesar el mensaje: {e}")
        pass # Simplemente ignoramos el mensaje y devolvemos 'ok'

    return "ok", 200


# 3️⃣ Lógica del Bot (Máquina de Estados)
def procesar_mensaje_calculadora(user, msg):
    
    # 1. Inicializar el estado del usuario si es nuevo
    if user not in usuarios:
        usuarios[user] = {"estado": "inicio", "datos": {}, "rubro": None}

    u = usuarios[user]

    # Estado inicial: Bienvenida
    if u["estado"] == "inicio":
        respuesta = ("👋 ¡Hola! Soy el bot para dividir los gastos de tu reunión.\n"
                     "Vamos a registrar por rubros: *Bebida, Comida y Postre*.\n"
                     "Escribí el rubro con el que querés empezar.")
        u["estado"] = "esperando_rubro"
        send_message(user, respuesta)
        return

    # Elegir rubro
    if u["estado"] == "esperando_rubro":
        if msg in ["bebida", "comida", "postre"]:
            u["rubro"] = msg
            respuesta = (f"Perfecto 🍻 Ingresá los gastos del rubro *{msg.upper()}*.\n"
                         "Formato: Nombre monto (ej: Juan 2500)\n"
                         "Cuando termines, escribí 'fin'.")
            u["estado"] = "ingresando_gastos"
            u["datos"][msg] = {}
        else:
            respuesta = "Por favor, escribí uno de estos rubros: *Bebida, Comida o Postre*."
        send_message(user, respuesta)
        return

    # Registrar gastos
    if u["estado"] == "ingresando_gastos":
        if msg == "fin":
            respuesta = "¿Querés agregar otro rubro? (*si*/ *no*)"
            u["estado"] = "otro_rubro"
        else:
            try:
                nombre, monto = msg.split()
                monto = float(monto)
                u["datos"][u["rubro"]][nombre.capitalize()] = u["datos"][u["rubro"]].get(nombre.capitalize(), 0) + monto
                respuesta = f"Registrado: {nombre.capitalize()} gastó ${monto:.2f} en {u['rubro'].capitalize()}."
            except ValueError:
                respuesta = "Formato incorrecto. Debés escribir *Nombre* *monto* (ej: Juan 2500)"
        send_message(user, respuesta)
        return

    # Agregar otro rubro o finalizar
    if u["estado"] == "otro_rubro":
        if msg in ["si", "sí"]:
            respuesta = "Decime el nombre del próximo rubro: *Bebida*, *Comida* o *Postre*."
            u["estado"] = "esperando_rubro"
        elif msg == "no":
            # Calcular totales
            resumen = calcular_balance_general(u["datos"])
            send_message(user, resumen)
            usuarios.pop(user)  # Limpiar sesión
            return
        else:
            respuesta = "Respondé *sí* o *no*."
        send_message(user, respuesta)
        return


# 4️⃣ Función para enviar mensajes (Adaptada de tu script anterior)
def send_message(to, text):
    url = f"https://graph.facebook.com/v20.0/{ID_NUMERO_TELEFONO}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
    except requests.exceptions.HTTPError as err:
        print(f"Error al enviar mensaje a WhatsApp: {err}")


# --- Funciones de Cálculo (Sin Cambios) ---
def calcular_balance_general(datos):
    total_general = 0
    gastos_por_persona = defaultdict(float)
    participantes = set()

    for rubro, gastos in datos.items():
        total_general += sum(gastos.values())
        for nombre, monto in gastos.items():
            gastos_por_persona[nombre] += monto
            participantes.add(nombre)

    n = len(participantes)
    if n == 0:
        return "No se ingresaron datos."

    por_persona = total_general / n

    saldos = {p: round(gastos_por_persona[p] - por_persona, 2) for p in participantes}
    
    texto = "📊 *Balance general:*\n"
    for p, s in saldos.items():
        estado = "recibe" if s < 0 else "paga" # Si el saldo es NEGATIVO, le deben; si es POSITIVO, debe pagar para equilibrar.
        texto += f"- {p}: {estado} ${abs(s):.2f}\n"

    transferencias = generar_transferencias(saldos)
    texto += "\n💸 *Propuesta de transferencias:*\n"
    for deudor, acreedor, monto in transferencias:
        texto += f"- {deudor} → {acreedor}: ${monto:.2f}\n"

    texto += "\n✅ ¡Listo! Todos los saldos quedan equilibrados."
    return texto


def generar_transferencias(saldos):
    # Acreedores (tienen saldo negativo, se les debe) y Deudores (tienen saldo positivo, deben pagar)
    acreedores = sorted([(p, s) for p, s in saldos.items() if s < 0], key=lambda x: x[1])
    deudores = sorted([(p, s) for p, s in saldos.items() if s > 0], key=lambda x: -x[1])
    
    transferencias = []
    i, j = 0, 0
    while i < len(deudores) and j < len(acreedores):
        deudor, deuda = deudores[i]
        acreedor, credito = acreedores[j]
        
        # Las deudas son positivas, los créditos son negativos
        monto = min(deuda, abs(credito))
        
        transferencias.append((deudor, acreedor, monto))
        
        deudores[i] = (deudor, deuda - monto)
        acreedores[j] = (acreedor, credito + monto)
        
        if deudores[i][1] == 0:
            i += 1
        if acreedores[j][1] == 0:
            j += 1
            
    return transferencias


if __name__ == "__main__":
    # La ejecución debe ser vía Gunicorn, pero mantenemos esto por si corres localmente.
    # En Docker, Gunicorn toma el control.
    app.run(host="0.0.0.0", port=5000)