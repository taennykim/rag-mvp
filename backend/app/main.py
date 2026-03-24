from fastapi import FastAPI


app = FastAPI(title="Insurance Document RAG MVP API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/upload")
def get_upload_status() -> dict[str, object]:
    return {
        "page": "upload",
        "status": "not_implemented",
        "message": "Upload API skeleton is ready.",
    }


@app.get("/chat")
def get_chat_status() -> dict[str, object]:
    return {
        "page": "chat",
        "status": "not_implemented",
        "message": "Chat API skeleton is ready.",
    }


@app.get("/evaluation")
def get_evaluation_status() -> dict[str, object]:
    return {
        "page": "evaluation",
        "status": "not_implemented",
        "message": "Evaluation API skeleton is ready.",
    }
