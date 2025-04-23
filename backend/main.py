import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .routes import bp  # 상대 import 사용

def create_app(config: str = "development") -> Flask:
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    app = Flask(__name__)
    app.config["ENV"] = config
    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024**2

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

    app.register_blueprint(bp)

    @app.route("/ping")
    def ping():
        return {"pong": True}, 200

    return app

if __name__ == "__main__":
    create_app().run(debug=True, host="0.0.0.0", port=5000)
