import os
import base64
from io import BytesIO
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores.utils import filter_complex_metadata
import pymupdf4llm
import re
from typing import List, Dict
import concurrent.futures

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

class CombinedEmbeddings(Embeddings):
    def __init__(self, text_embeddings, documents):
        self.text_embeddings = text_embeddings
        self.documents = documents

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        text_embedding = self.text_embeddings.embed_query(text)
        doc = next((doc for doc in self.documents if doc.page_content == text), None)
        if doc:
            image_embeddings = doc.metadata.get("image_embeddings", [])
            if image_embeddings:
                combined = text_embedding + sum(image_embeddings, [])
                return combined
        return text_embedding

def extract_pdf_content(file_path: str) -> List[Dict]:
    try:
        pdf_content = pymupdf4llm.to_markdown(
            file_path,
            page_chunks=True,
            write_images=True,
            embed_images=True
        )
        
        def process_page(page_data):
            return {
                'page_number': page_data['metadata']['page'],
                'content': page_data['text'],
                'images': extract_image_b64(page_data['text'])
            }
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            processed_content = list(executor.map(process_page, pdf_content))
        
        print(f"Extracted content from PDF file. {len(processed_content)} pages")
        return processed_content
    
    except Exception as e:
        print(f"An error occurred while processing the PDF: {str(e)}")
        return []

def extract_image_b64(content: str) -> List[str]:
    image_pattern = r"data:image\/[a-zA-Z]+;base64,([^`\s]+)"
    return re.findall(image_pattern, content)

def split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_text(text)

def decode_base64_image(b64_string):
    image_data = base64.b64decode(b64_string)
    return Image.open(BytesIO(image_data)).convert("RGB")

def get_image_embedding(image: Image.Image):
    try:
        inputs = clip_processor(images=image, return_tensors="pt")
        outputs = clip_model.get_image_features(**inputs)
        normalized_embedding = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
        return normalized_embedding.detach().cpu().numpy()
    except Exception as e:
        print(f"Error processing an image: {e}")
        return None

def create_documents(pdf_content):
    documents = []
    for page in pdf_content:
        text_content = page['content']
        image_embeddings = []
        for image_b64 in page['images']:
            image = decode_base64_image(image_b64)
            image_embedding = get_image_embedding(image)
            if image_embedding is not None:
                image_embeddings.append(image_embedding.flatten().tolist())
        
        doc = Document(
            page_content=text_content,
            metadata={
                "page": page['page_number'],
                "source": "PDF",
                "image_embeddings": image_embeddings
            }
        )
        documents.append(doc)
    return documents

def main():
    file_path = "input.pdf"
    pdf_content = extract_pdf_content(file_path)

    # Process text and images
    documents = create_documents(pdf_content)

    # Initialize embeddings and Chroma DB
    text_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    combined_embeddings = CombinedEmbeddings(text_embeddings, documents)

    # Filter complex metadata
    filtered_documents = filter_complex_metadata(documents)

    # Create Chroma vectorstore with filtered documents
    vectorstore = Chroma.from_documents(filtered_documents, combined_embeddings, persist_directory="./chroma_db")

    # Create a retriever and QA chain
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever)

    # User query
    query = input("Enter your query: ")
    result = qa_chain({"query": query})

    # Get relevant documents
    relevant_docs = retriever.get_relevant_documents(query)

    # Preview the pages from where relevant documents are fetched
    print("\nRelevant Documents:")
    for i, doc in enumerate(relevant_docs):
        print(f"Document {i + 1}:")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Page: {doc.metadata.get('page', 'Unknown')}")
        print(f"Preview: {doc.page_content[:200]}...")
        print()

    print("Answer:", result["result"])

if __name__ == "__main__":
    main()
