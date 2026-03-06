import os
from src.utils.chatbot_utils import BuildChatbot
from src.utils.logger import logging
from src.utils.exception import Custom_exception

from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    redirect,
    url_for,
    session,
    flash,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv


# load environment variables from .env (if present)
load_dotenv()


# initializing flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_secret_key")

# MySQL DB for users (configured via environment variables)
db_user = os.environ.get("DB_USER") or os.environ.get("MYSQL_USER", "root")
db_password = (
    os.environ.get("DB_PASSWORD")
    or os.environ.get("MYSQL_PASSWORD")
    or os.environ.get("MYSQL_ROOT_PASSWORD", "")
)
db_host = os.environ.get("DB_HOST") or os.environ.get("MYSQL_HOST", "localhost")
db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQL_PORT", "3306")
db_name = os.environ.get("DB_NAME") or os.environ.get(
    "MYSQL_DB", "ecommerce_recommender_system"
)

# construct SQLAlchemy URI, prefer using pymysql driver
if db_password:
    db_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
else:
    # allow empty password (not recommended for production)
    db_uri = f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# setting up the chatbot(retriever)
chatbot = None
try:
    utils = BuildChatbot()
    chatbot = utils.initialize_chatbot()
    logging.info("Chatbot initialized successfully!")
except Exception as e:
    logging.error(f"Failed to initialize chatbot: {str(e)}")
    logging.error("ERROR: Required API keys or Pinecone index not found.")
    logging.error("Please ensure:")
    logging.error("1. HF_API_KEY is set correctly in .env file")
    logging.error("2. Pinecone index 'Ecommerce-Recommender-System' exists")
    logging.error("3. PINECONE_API_KEY is correct")
    logging.error("\nTo create the Pinecone index, run:")
    logging.error("  python -m src.components.vectorstore_builder")


# ensure DB tables exist
with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass


# route for home page
@app.route("/")
def home():
    return render_template("home_page.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        role = request.form.get("role", "user")

        if not username or not password:
            flash("Username and password are required.")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.")
            return render_template("register.html")

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists. Choose another.")
            return render_template("register.html")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role if role in ["user", "admin"] else "user",
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password")
            return render_template("login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        flash("Logged in successfully.")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if chatbot is None:
        return (
            jsonify(
                {
                    "error": "Chatbot not initialized. Please check configuration and API keys."
                }
            ),
            500,
        )

    data = request.get_json()
    question = data.get("input", "")
    logging.info(f"User Input: {question}")

    config = {"configurable": {"session_id": "chat_1"}}

    response = chatbot.invoke({"input": question}, config=config)

    logging.info(f"Chatbot Response: {response['answer']}")

    return jsonify({"response": response["answer"]})


if __name__ == "__main__":
    # for local development
    # app.run(debug=True, use_reloader=False)

    # for production, port should match with inbound rule of ec2 instance
    app.run(host="0.0.0.0", port=8000, debug=False)
