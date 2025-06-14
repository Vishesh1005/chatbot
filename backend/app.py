from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import traceback
import sqlite3
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEmbeddings

# ======== Load environment variables ========
load_dotenv()

# ======== FastAPI App Initialization ========
app = FastAPI()

# CORS config for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vishesh1005.github.io"],  # Replace if custom domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== Lazy Load Vectorstore Function ========
def load_vectordb():
    print("🧠 Loading vector store...")
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    index_path = os.path.join(os.path.dirname(__file__), "Documents", "vectorstore")
    return FAISS.load_local(
        folder_path=index_path,
        embeddings=embedding,
        allow_dangerous_deserialization=True
    )

# ======== SQLite Connection ========
db_path = os.path.join(os.path.dirname(__file__), "data.db")
try:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT
        );
    """)
    conn.commit()
    print("✅ SQLite connected.")
except Exception as e:
    print("❌ SQLite connection failed:", e)
    conn = None
    cursor = None

# ======== Request Schema ========
class Message(BaseModel):
    text: str

# ======== Chat Endpoint ========
@app.post("/chat")
async def chat(msg: Message):
    try:
        print("💬 User query:", msg.text)

        vectordb = load_vectordb()

        llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="togethercomputer/llama-2-7b-chat",  # Or try Mixtral
            temperature=0.3
        )

        qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
        response = qa.run(msg.text)
        print("✅ Response:", response)

        return {"response": response}
    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Server error. Please try again later."}

# ======== Form Submission Endpoint ========
@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if cursor is None:
        return JSONResponse(content={"message": "❌ DB not available"}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        conn.commit()
        return JSONResponse(content={"message": "Form submitted successfully!"})
    except Exception as e:
        print("❌ DB error:", e)
        return JSONResponse(content={"message": f"DB Error: {str(e)}"}, status_code=500)
