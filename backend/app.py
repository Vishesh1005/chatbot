from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os, traceback, sqlite3
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_together import ChatTogether

# Load .env
load_dotenv()

app = FastAPI()

# CORS for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vishesh1005.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route so Render doesn’t shut down
@app.get("/")
def read_root():
    return {"message": "ITS Admission Chatbot is Live!"}

# DB setup (SQLite)
try:
    db = sqlite3.connect("data.db", check_same_thread=False)
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT
        )
    """)
    db.commit()
    print("✅ SQLite connected.")
except Exception as e:
    print("❌ SQLite error:", e)
    db = None
    cursor = None

# Load FAISS index
vectordb = None
try:
    print("🧠 Loading embeddings...")
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = FAISS.load_local(
        folder_path="backend/Documents/vectorstore",
        embeddings=embedding,
        allow_dangerous_deserialization=True
    )
    print("✅ FAISS index loaded.")
except Exception as e:
    print("❌ FAISS load error:", e)
    traceback.print_exc()

# Chat request body
class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat(msg: Message):
    if vectordb is None:
        return {"response": "❌ FAISS index not available."}
    try:
        print("💬 User:", msg.text)

        llm = ChatTogether(
            model="togethercomputer/llama-2-7b-chat",
            temperature=0.2,
            together_api_key=os.getenv("TOGETHER_API_KEY")
        )

        chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=vectordb.as_retriever()
        )

        result = chain.run(msg.text)
        print("✅ Bot:", result)
        return {"response": result}

    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Server error. Please try again later."}

@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if cursor is None:
        return JSONResponse(content={"message": "❌ DB unavailable."}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        db.commit()
        return JSONResponse(content={"message": "✅ Form submitted."})
    except Exception as e:
        return JSONResponse(content={"message": f"❌ DB error: {e}"}, status_code=500)
