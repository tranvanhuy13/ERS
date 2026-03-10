import sys

import os
from src.components.data_collection import DataCollection
from src.components.data_cleaning import DataCleaner
from src.components.vectorstore_builder import VectorStoreBuilder
from src.components.chatbot_builder import ChatbotBuilder
from src.utils.chatbot_utils import BuildChatbot

from src.utils.logger import logging
from src.utils.exception import Custom_exception
from dotenv import load_dotenv

load_dotenv()


def main():
    try:
        # Optionally run data collection (scraper -> MySQL). Set env var RUN_DATA_COLLECTION=true to enable.
        if os.getenv("RUN_DATA_COLLECTION", "false").lower() == "true":
            data_collection = DataCollection()
            data_collection.initiate_data_collection()

        data_cleaner = DataCleaner()
        data_cleaner.clean_data()

        vectorstore_builder = VectorStoreBuilder()
        vector_store = vectorstore_builder.run_pipeline()

        # Use the Runnable-based chatbot wrapper which provides `invoke`
        chatbot_builder = BuildChatbot()
        chatbot = chatbot_builder.initialize_chatbot()

        # test code (provide session_id in config for RunnableWithMessageHistory)
        test_response = chatbot.invoke(
            {"input": "What do you do?"},
            {"configurable": {"session_id": "test_session"}},
        )

        logging.info(f"Test Response: {test_response}")
        print("Test response: ", test_response)

    except Exception as e:
        raise Custom_exception(e, sys)


if __name__ == "__main__":
    main()
