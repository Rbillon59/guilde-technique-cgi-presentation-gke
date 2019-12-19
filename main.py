from flask import Flask
import os
import random

app = Flask(__name__)


@app.route("/hello")
def hello():
    if not os.environ.get("myEnvironmentVariable"):
        return "Hello CGI"
    return os.environ.get("myEnvironmentVariable")


@app.route("/secret")
def secret():
    return os.environ.get("SECRET_USERNAME")


@app.route("/config")
def config():
    return os.environ.get("CONFIG_MAP")

@app.route("/compute")
def compute():
    i = 0
    result = random.randint(1, 100)
    for i in range(1,1000000):
        x = random.randint(1, 100)
        y = random.randint(1, 10)
        i = i + 1
        result = x ** y / result
        result = result +1
    return str(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
