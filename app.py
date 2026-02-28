import os
from src.utils.chatbot_utils import BuildChatbot
from src.utils.logger import logging
from src.utils.exception import Custom_exception

from flask import Flask, request, render_template, jsonify


# initializing flask app
app = Flask(__name__)

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


# route for home page
@app.route("/")
def home():
    return render_template("home_page.html")


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
