from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

app = FastAPI()

# ✅ CORS FIX: Allow GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://vishesh1005.github.io"],  # 👈 GitHub Pages domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Lazy-load paths only
index_path = os.path.join(os.path.dirname(__file__), "Documents", "index")

# ✅ DB Connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Vishesh@1005",
        database="chatbot",
        connection_timeout=5
    )
    cursor = db.cursor()
    print("✅ MySQL connected.")
except Exception as e:
    print("❌ MySQL connection failed:", e)
    db = None
    cursor = None

# ======== Data Model ========
class Message(BaseModel):
    text: str

# ======== Chat Route ========
@app.post("/chat")
async def chat(msg: Message):
    try:
        # ✅ Lazy load to save memory
        embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectordb = FAISS.load_local(
            folder_path=index_path,
            embeddings=embedding,
            allow_dangerous_deserialization=True
        )

        llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.3
        )

        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
        result = qa_chain.invoke({"query": msg.text})

        return {"response": result}

    except Exception as e:
        print("❌ Chat error:", e)
        return {"response": "⚠️ Server error. Please try again later."}

# ======== Form Submit Route ========
@app.post("/submit-form")
async def submit_form(name: str = Form(...), email: str = Form(...), phone: str = Form(...)):
    if cursor is None:
        return JSONResponse(content={"message": "❌ Database connection not available."}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
        db.commit()
        return JSONResponse(content={"message": "Form submitted successfully!"})
    except Exception as e:
        return JSONResponse(content={"message": f"Database Error: {str(e)}"}, status_code=500)
