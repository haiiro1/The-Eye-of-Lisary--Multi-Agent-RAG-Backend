from langfuse.langchain import CallbackHandler

def get_langfuse_callback(session_id: str):
    handler = CallbackHandler()
    handler.session_id = session_id
    return handler