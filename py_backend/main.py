import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from pdfUpload import extract_pdf_content, create_documents, CombinedEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.chains import RetrievalQA
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

origins = [
    "http://localhost:5173",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_FOLDER = "uploads"
CHROMA_DB_DIR = "./chroma_db"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

text_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

documents = []
vectorstore = None
retriever = None
qa_chain = None

class QueryRequest(BaseModel):
    file_id: str
    query: str

class RelevantDocument(BaseModel):
    source: str
    page: int
    preview: str

class QueryResponse(BaseModel):
    answer: str
    relevant_docs: List[RelevantDocument]

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.pdf")  
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    try:
        pdf_content = extract_pdf_content(file_path)
        documents = create_documents(pdf_content)
        text_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        combined_embeddings = CombinedEmbeddings(text_embeddings, documents)
        filtered_documents = filter_complex_metadata(documents)
        Chroma.from_documents(filtered_documents, combined_embeddings, persist_directory=f"./chroma_db_{file_id}")
        return {"file_id": file_id}
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    file_path = os.path.join(UPLOAD_FOLDER, f"{request.file_id}.pdf") 
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        text_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
        vectorstore = Chroma(persist_directory=f"./chroma_db_{request.file_id}", embedding_function=text_embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
        qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)
        
        result = qa_chain({"query": request.query})
        relevant_docs = retriever.get_relevant_documents(request.query)
        
        return QueryResponse(
            answer=result["result"],
            relevant_docs=[
                RelevantDocument(
                    source=doc.metadata.get('source', 'Unknown'),
                    page=doc.metadata.get('page', 'Unknown'),
                    preview=doc.page_content[:200]
                )
                for doc in relevant_docs
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
