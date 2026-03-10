from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_chat_history(session_id: str):
    # Crea un archivo 'chat_history.db' automáticamente
    return SQLChatMessageHistory(
        session_id=session_id,
        connection="sqlite:///data/chat_history.db"
    )