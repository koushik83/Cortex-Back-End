from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
from app.bot import process_message, add_company_knowledge
from app.processor import process_document

app = FastAPI(title="Simple Company Chatbot")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for request/response
class ChatMessage(BaseModel):
    message: str
    company_id: str

class ChatResponse(BaseModel):
    response: str
    confidence: float
    context: str
    source: str

@app.post("/setup/{company_id}")
async def setup_company(company_id: str, files: List[UploadFile]):
    """Setup endpoint for companies to upload their documents"""
    try:
        texts = []
        sources = []
        print(f"Processing files for company: {company_id}")
        
        for file in files:
            print(f"Processing file: {file.filename}")
            content = await file.read()
            text, source = process_document(content, file.filename, file.content_type)
            texts.append(text)
            sources.append(source)
        
        success = add_company_knowledge(company_id, texts, sources)
        if success:
            return {"status": "success", "message": f"Setup complete for company {company_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to process documents")
            
    except Exception as e:
        print(f"Setup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage):
    """Chat endpoint that handles user messages"""
    try:
        response, confidence, context, source = process_message(chat.company_id, chat.message)
        return ChatResponse(
            response=response,
            confidence=confidence,
            context=context,
            source=source
        )
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{company_id}")
async def get_analytics(company_id: str):
    """Get chat analytics for a company"""
    try:
        from app.bot import get_analytics
        return get_analytics(company_id)
    except Exception as e:
        print(f"Analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)