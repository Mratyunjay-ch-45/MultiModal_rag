import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pymupdf4llm import to_markdown
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
import pdfUpload as pd


# Create the FastAPI app
app = FastAPI()

origins = [
    "http://localhost:5173",  # Your frontend URL
    # Add any other origins you need to allow
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Allows requests from these origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize embeddings and Chroma vector store
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        pdf_content = pd.extract_pdf_content(file_path)
        documents = pd.create_documents(pdf_content)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error processing PDF: {str(e)}"})

    documents = []
    for page_data in pdf_content:
        page_number = page_data.get('metadata', {}).get('page', None)
        content = page_data.get('text', '')
        if page_number is None:
            continue
        documents.append({
            "text": content,
            "metadata": {"page": page_number, "source": file.filename}
        })

    # Add the documents to the vector store
    try:
        vectorstore.add_documents(documents)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error adding documents: {str(e)}"})

    return {"message": "PDF uploaded and processed", "filename": file.filename}

@app.post("/query")
async def query_pdf(query: str = Form(...)):
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
        result = qa_chain({"query": query})
        relevant_docs = retriever.get_relevant_documents(query)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Query failed: {str(e)}"})

    response = {
        "answer": result.get("result", ""),
        "documents": [
            {"page": doc.metadata.get("page"), "content": doc.page_content} for doc in relevant_docs
        ]
    }
    return JSONResponse(content=response)

# A simple root endpoint to test the server
@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}
