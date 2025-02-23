import pymupdf4llm
import os
import base64
from io import BytesIO
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def extract_pdf_content(file_path):
    
    pdf_content = pymupdf4llm.to_markdown(
        file_path,
        page_chunks=True,
        write_images=True,
        embed_images=True
    )
    
    return pdf_content

def split_text_into_chunks(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

def get_text_embedding(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    print("Embedding text chunks done...")
    return [embeddings.embed_query(chunk) for chunk in text_chunks]    


def extract_text(markdown_content):
    
    texts = []
    if isinstance(markdown_content, list):
        for item in markdown_content:
            if isinstance(item, dict):
                
                if "text" in item and isinstance(item["text"], str):
                    texts.append(item["text"])
                elif "content" in item and isinstance(item["content"], str):
                    texts.append(item["content"])
                else:
                    
                    texts.append(str(item))
            elif isinstance(item, str):
                texts.append(item)
    elif isinstance(markdown_content, str):
        texts = [markdown_content]
    else:
        raise ValueError("Unsupported type for markdown_content")
    
    
    combined_text = "\n".join(texts)
    
    
    text_only = re.sub(r"!\[.*?\]\(data:image\/[a-zA-Z]+;base64,[^`\s]+\)", "", combined_text)
    
    return text_only



def extract_image_b64(markdown_content):
   
    image_b64_list = []
    image_pattern = r"data:image\/[a-zA-Z]+;base64,([^`\s]+)"
    
    
    if isinstance(markdown_content, list):
        for item in markdown_content:
            
            if isinstance(item, dict):
                
                for key in ["text", "content"]:
                    if key in item and isinstance(item[key], str):
                        found = re.findall(image_pattern, item[key])
                        image_b64_list.extend(found)
            elif isinstance(item, str):
                found = re.findall(image_pattern, item)
                image_b64_list.extend(found)
    
    
    elif isinstance(markdown_content, dict):
        for key, value in markdown_content.items():
            if isinstance(value, str):
                found = re.findall(image_pattern, value)
                image_b64_list.extend(found)
            elif isinstance(value, list):
                
                for sub_item in value:
                    if isinstance(sub_item, str):
                        found = re.findall(image_pattern, sub_item)
                        image_b64_list.extend(found)
                    elif isinstance(sub_item, dict):
                        for sub_key in ["text", "content"]:
                            if sub_key in sub_item and isinstance(sub_item[sub_key], str):
                                found = re.findall(image_pattern, sub_item[sub_key])
                                image_b64_list.extend(found)
    
    else:
        
        if isinstance(markdown_content, str):
            found = re.findall(image_pattern, markdown_content)
            image_b64_list.extend(found)
    
    # print("Extracted Base64 images:", image_b64_list)
    return image_b64_list

def decode_base64_image(b64_string):
    
    image_data = base64.b64decode(b64_string)
    image = Image.open(BytesIO(image_data)).convert("RGB")
    return image

def get_image_embedding(image: Image.Image):
    
    inputs = clip_processor(images=image, return_tensors="pt")
    outputs = clip_model.get_image_features(**inputs)
    
    normalized_embedding = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
    return normalized_embedding.detach().cpu().numpy()


file_path = "input.pdf"
markdown_content = extract_pdf_content(file_path)
image_b64_list = extract_image_b64(markdown_content)
extract_text= extract_text(markdown_content)
if extract_text:
    print("Extracted Text",extract_text)
else:
    print("No text found in the PDF file.")
text_chunks = split_text_into_chunks(extract_text)
text_embeddings = get_text_embedding(text_chunks)
print("Generated embeddings for", len(text_embeddings), "text chunks.")        


image_embeddings = []
for b64_str in image_b64_list:
    try:
        image = decode_base64_image(b64_str)
        embedding = get_image_embedding(image)
        image_embeddings.append(embedding)
        
    except Exception as e:
        print("Error processing an image:", e)

# print(image_embeddings)

print("Generated embeddings for", len(image_embeddings), "images.")
