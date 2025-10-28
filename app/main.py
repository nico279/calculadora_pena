from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["GET"])
def verify():
    print("=== GET VERIFICATION ===")
    for k, v in request.args.items():
        print(f"{k} = {v}")
    if request.args.get("hub.verify_token") == "27148101":
        return request.args.get("hub.challenge")
    return "Token inválido", 403
