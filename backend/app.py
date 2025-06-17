from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import traceback
import sqlite3
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_together import ChatTogether
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse


# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ===== Set Hugging Face cache path =====
os.environ["TRANSFORMERS_CACHE"] = "/tmp/hf"
os.environ["HF_HOME"] = "/tmp/hf"

# ===== Load embeddings =====

# ======== Load FAISS Vector Index and Embeddings ========
print("🧑‍🧠 Loading embeddings...")
from langchain_huggingface import HuggingFaceEmbeddings
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
index_path = os.path.join(os.path.dirname(__file__), "Documents", "vectorstore")
print("🚣️ FAISS index path:", index_path)

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

# ======== Connect to SQLite ========
print("🗄️ Connecting to SQLite...")
try:
    import shutil

    # Original read-only path
    readonly_path = os.path.join(os.path.dirname(__file__), "data.db")
    # Writable copy path
    writable_path = "/tmp/data.db"

    # Copy to writable location if not already copied
    if not os.path.exists(writable_path):
        shutil.copyfile(readonly_path, writable_path)

    # Connect to writable copy
    conn = sqlite3.connect(writable_path)
    cursor = conn.cursor()

    print("✅ SQLite connected.")
except Exception as e:
    print("❌ SQLite connection failed:", e)
    conn = None
    cursor = None


# ======== Request Data Model ========
class Message(BaseModel):
    text: str

# ======== Chat Endpoint ========
@app.post("/chat")
async def chat(msg: Message):
    if vectordb is None:
        return {"response": "❌ FAISS index not available."}

    text = msg.message.strip().lower()
    greetings = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]

    if text in greetings:
        return {"response": "Hello! I’m here to help with college admissions. You can ask about courses, fees, eligibility, or documents."}

    try:
        retriever = vectordb.as_retriever(search_kwargs={"k": 1})
        docs = retriever.get_relevant_documents(msg.text)

        if not docs:
            return {"response": "Sorry, I couldn’t find any information related to that. Try asking about fees, courses, or eligibility."}

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

        response = llm.invoke(prompt)
        return {"response": response.content}

    except Exception as e:
        print("❌ Chat error:", e)
        traceback.print_exc()
        return {"response": "⚠️ Server error. Please try again later."}

# ======== Form Submission Endpoint ========
class FormData(BaseModel):
    name: str
    email: str
    phone: str

@app.post("/submit-form")
async def submit_form(data: FormData):
    if cursor is None:
        return JSONResponse(content={"message": "❌ Database connection not available."}, status_code=500)
    try:
        cursor.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)", (data.name, data.email, data.phone))
        conn.commit()
        return {"message": "✅ Form submitted successfully!"}
    except Exception as e:
        return JSONResponse(content={"message": f"Database Error: {str(e)}"}, status_code=500)


#== form data ==#
@app.get("/submissions", response_class=HTMLResponse)
async def view_submissions(request: Request):
    password = request.query_params.get("key")

    if password != os.getenv("ADMIN_KEY"):  # Load from .env
        return HTMLResponse("<h3>❌ Access Denied: Invalid Key</h3>", status_code=401)

    if cursor is None:
        return "<h2>❌ Database connection not available.</h2>"


    try:
        cursor.execute("SELECT name, email, phone FROM users")
        rows = cursor.fetchall()

        html = """
        <html><head><title>Submissions</title>
        <style>
          table { border-collapse: collapse; width: 80%; margin: auto; }
          th, td { border: 1px solid #ccc; padding: 8px 12px; }
          th { background: #eee; }
          body { font-family: sans-serif; padding: 20px; text-align: center; }
        </style>
        </head><body><h2>Submitted User Details</h2><table>
        <tr><th>Name</th><th>Email</th><th>Phone</th></tr>
        """
        for row in rows:
            html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td></tr>"
        html += "</table></body></html>"

        return HTMLResponse(content=html)

    except Exception as e:
        return f"<h2>❌ Error: {str(e)}</h2>"
