# backend/app.py
from flask import Flask
from backend.routes import bp  # Blueprint는 routes.py로 분리할 수도 있음

app = Flask(__name__)
app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
