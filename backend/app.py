from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
import os
import traceback
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate


# Load environment variables (e.g., TOGETHER_API_KEY)
load_dotenv()



app = FastAPI()

# Enable CORS so frontend can talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======== Load FAISS Vector Index and Embeddings ========
print("🧠 Loading embeddings...")
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

index_path = os.path.join(os.path.dirname(__file__), "Documents", "vectorstore")
print("🛣️ FAISS index path:", index_path)

vectordb = None
if os.path.exists(index_path):
    try:
        print("📦 Loading FAISS index...")
        vectordb = FAISS.load_local(
            folder_path=index_path,
            embeddings=embedding,
            allow_dangerous_deserialization=True
        )
        print("✅ FAISS index loaded.")
    except Exception as e:
        print("❌ Failed to load FAISS index:", e)
        traceback.print_exc()
else:
    print("❌ FAISS folder not found. Please run create_index.py.")
    vectordb = None

# ======== Connect to MySQL ========
print("🗄️ Connecting to MySQL...")
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

# ======== Request Data Model ========
class Message(BaseModel):
    text: str

# ======== Chat Endpoint ========
@app.post("/chat")
async def chat(msg: Message):
    if vectordb is None:
        return {"response": "❌ FAISS index not available."}

    text = msg.text.strip().lower()
    greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]

    if text in greetings:
        return {"response": "Hello! I’m here to help with college admissions. You can ask about courses, fees, eligibility, or documents."}

    try:
        # ✅ Strict retrieval: top 1 chunk
        retriever = vectordb.as_retriever(search_kwargs={"k": 1})
        docs = retriever.get_relevant_documents(msg.text)

        if not docs:
            return {"response": "Sorry, I couldn’t find any information related to that. Try asking about fees, courses, or eligibility."}

        # ✅ Strict prompt (only answer, no hallucination)
        context = "\n\n".join([doc.page_content for doc in docs])
        question = msg.text.strip()

        prompt = (
            "You are an AI assistant for ITS College admissions.\n"
            "Only answer the question based on the context below.\n"
            "Do not invent answers. Do not ask for more personal info.\n"
            "Be concise. If unrelated, reply: 'I'm here to help with admissions only.'\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )

        llm = ChatTogether(
            together_api_key=os.getenv("TOGETHER_API_KEY"),
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.2
        )

        # ✅ Ensure we only return response.content
        response = llm.invoke(prompt)
        return {"response": response.content}

    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Server error. Please try again later."}


# ======== Form Submission Endpoint ========
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
