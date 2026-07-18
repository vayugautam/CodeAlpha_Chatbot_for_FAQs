from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from chatbot import FAQChatbot
import uvicorn
import os

app = FastAPI(title="FAQ Chatbot API")

# Initialize Chatbot
bot = FAQChatbot()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    reply = bot.get_best_answer(request.message)
    return ChatResponse(reply=reply)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files to serve the frontend UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
