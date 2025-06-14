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

# Load environment variables
load_dotenv()

app = FastAPI()

# ✅ CORS for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vishesh1005.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== Global Variables (lazy load on first request) ========
embedding = None
vectordb = None
qa_chain = None
llm = None

# ======== SQLite Setup ========
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
    print("❌ SQLite connection failed:", e)
    cursor = None

# ======== Input Model ========
class Message(BaseModel):
    text: str

# ======== Lazy Init Function ========
def init_chain():
    global embedding, vectordb, qa_chain, llm

    if not embedding:
        print("🧠 Loading embeddings...")
        embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    if not vectordb:
        index_path = os.path.join(os.path.dirname(__file__), "Documents", "vectorstore")
        if not os.path.exists(index_path):
            raise RuntimeError("❌ FAISS vectorstore not found. Please run create_index.py")
        print("📦 Loading FAISS index...")
        vectordb = FAISS.load_local(folder_path=index_path, embeddings=embedding, allow_dangerous_deserialization=True)

    if not llm:
        print("🤖 Loading Together.ai LLaMA 2...")
        llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="meta-llama/Llama-2-7b-chat-hf",
            temperature=0.0
        )

    if not qa_chain:
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
        print("✅ QA chain ready.")

# ======== Chat Endpoint ========
@app.post("/chat")
async def chat(msg: Message):
    try:
        init_chain()
        print("💬 User question:", msg.text)
        response = qa_chain.invoke(msg.text)
        return {"response": response}
    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Server error. Please try again later."}

# ======== Form Submission Endpoint ========
@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if not cursor:
        return JSONResponse(content={"message": "❌ Database connection not available."}, status_code=500)

    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        conn.commit()
        return JSONResponse(content={"message": "Form submitted successfully!"})
    except Exception as e:
        return JSONResponse(content={"message": f"Database Error: {str(e)}"}, status_code=500)
