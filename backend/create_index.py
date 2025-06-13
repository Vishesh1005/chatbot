import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

# Set up embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load your documents
file_path = os.path.join(os.path.dirname(__file__), "Documents", "admission_mock.txt")  # your data file
loader = TextLoader(file_path)
docs = loader.load()

# Split documents into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_docs = text_splitter.split_documents(docs)

# Create FAISS vector store
db = FAISS.from_documents(split_docs, embedding_model)

# Save index to backend/Documents/index
index_path = os.path.join(os.path.dirname(__file__), "Documents", "index")
db.save_local(index_path)

print("✅ Index created successfully.")
