from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/chat")
def chat():
    message = request.args.get("message")
    print(message)
    return jsonify({"message": message})

if __name__ == "__main__":
    app.run()