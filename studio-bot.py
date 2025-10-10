from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/chat")
def chat():
    args = request.get_json()
    message = args["message"]
    print("message")

if __name__ == "__main__":
    app.run()