from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
import os
from dotenv import load_dotenv
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

import urllib.parse
import os

try:
    db_url = os.getenv("DATABASE_URL")
    parsed_url = urllib.parse.urlparse(db_url)

    db = psycopg2.connect(
        dbname=parsed_url.path[1:],
        user=parsed_url.username,
        password=parsed_url.password,
        host=parsed_url.hostname,
        port=parsed_url.port
    )
    cursor = db.cursor()
    print("✅ PostgreSQL connected.")


# ======== Data Model ========
class Message(BaseModel):
    text: str

# ======== Chat Route ========
@app.post("/chat")
async def chat(msg: Message):
    try:
        print("💬 Received question:", msg.text)

        # ✅ Lazy load on each request
        from langchain_community.vectorstores import FAISS
        from langchain.chains import RetrievalQA
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_together import ChatTogether

        # Load embedding and FAISS index
        embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectordb = FAISS.load_local(
            folder_path=index_path,
            embeddings=embedding,
            allow_dangerous_deserialization=True
        )

        # Load LLM
        llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.3
        )

        # Create chain and get answer
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectordb.as_retriever())
        response = qa_chain.invoke({"query": msg.text})

        return {"response": response}

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
