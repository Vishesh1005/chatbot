from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import mysql.connector

from langchain.chains import RetrievalQA
from langchain_together import ChatTogether

# Do NOT load these at startup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals — load later
vectordb = None
embedding = None

# MySQL
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vishesh@1005",
        database="chatbot"
    )
    cursor = db.cursor()
except:
    cursor = None

# Models
class Message(BaseModel):
    text: str

# Chat endpoint
@app.post("/chat")
async def chat(msg: Message):
    global vectordb, embedding

    if vectordb is None:
        print("🧠 Lazy-loading embedding & FAISS...")
        embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        index_path = os.path.join(os.path.dirname(__file__), "Documents", "index")
        vectordb = FAISS.load_local(
            folder_path=index_path,
            embeddings=embedding,
            allow_dangerous_deserialization=True
        )

    llm = ChatTogether(
        together_api_key=os.getenv("TOGETHER_API_KEY"),
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.2
    )
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
    result = qa_chain.invoke({"query": msg.text})

    return {"response": result["result"]}

# Form submission
@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if cursor is None:
        return JSONResponse(content={"message": "Database not connected."}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
        db.commit()
        return JSONResponse(content={"message": "Form submitted successfully!"})
    except Exception as e:
        return JSONResponse(content={"message": f"Database Error: {str(e)}"}, status_code=500)
