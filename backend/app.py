from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import sqlite3
from dotenv import load_dotenv
import traceback

from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEmbeddings

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

# DB setup
try:
    db_path = os.path.join(os.path.dirname(__file__), "data.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT
        )
    """)
    conn.commit()
    print("✅ SQLite connected.")
except Exception as e:
    print("❌ SQLite error:", e)
    cursor = None

# Input model
class Message(BaseModel):
    text: str

# Global lazy init vars
embedding = None
vectordb = None
qa_chain = None

@app.post("/chat")
async def chat(msg: Message):
    global embedding, vectordb, qa_chain
    try:
        print("💬 User:", msg.text)

        if not embedding:
            print("🧠 Loading embedding...")
            embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        if not vectordb:
            print("📦 Loading FAISS index...")
            index_path = os.path.join(os.path.dirname(__file__), "Documents", "vectorstore")
            vectordb = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True)
            print("✅ FAISS loaded.")

        if not qa_chain:
            print("⚙️ Loading LLM...")
            llm = ChatTogether(
                together_api_key=os.getenv("TOGETHER_API_KEY"),
                model="meta-llama/Llama-2-7b-chat-hf",
                temperature=0.0
            )
            qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
            print("✅ QA chain ready.")

        response = qa_chain.run(msg.text)
        return {"response": response}

    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "❌ Server error. Please try again later."}


@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if cursor is None:
        return JSONResponse(content={"message": "❌ Database unavailable"}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        conn.commit()
        return JSONResponse(content={"message": "Form submitted!"})
    except Exception as e:
        return JSONResponse(content={"message": f"❌ DB error: {e}"}, status_code=500)
