import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Autotest-monster Platform",
    description="Enterprise AI Test Platform Backend",
    version="0.1.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Autotest-monster Platform API is Running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- Demo: Enterprise Task Parser ---
from pydantic import BaseModel
from core.parser import EnterpriseTaskParser

class ParseRequest(BaseModel):
    instruction: str
    context_snapshot: str = None # Base64 image placeholder

@app.post("/api/ai/parse")
async def parse_instruction_endpoint(request: ParseRequest):
    # Initialize parser (API Key would be injected from Env/Settings here)
    parser = EnterpriseTaskParser(ai_api_key=None) 
    result = await parser.parse(request.instruction)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
