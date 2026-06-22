import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any

from database import get_db, is_mock
from agents.orchestrator import CampaignOrchestrator
from agents.identity_agent import IdentityStitchingAgent

app = FastAPI(title="Aura Agentic MarTech API", version="1.0.0")

# Enable CORS for local React/Vite development and production UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    email: EmailStr
    event_type: str
    event_data: Dict[str, Any]

class CampaignRequest(BaseModel):
    email: EmailStr

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "mock_in_memory" if is_mock else "supabase_postgres"
    }

@app.get("/api/profiles")
def get_profiles():
    db = get_db()
    # In Mock db, data is in memory, in real supabase it's fetched
    response = db.table("customer_profiles").select().execute()
    # Handle response format variations
    profiles = response.data if hasattr(response, 'data') else response
    return {"profiles": profiles}

@app.post("/api/ingest")
def ingest_touchpoint(req: IngestRequest):
    db = get_db()
    
    # Store raw touchpoint event
    touchpoint_data = {
        "email": req.email,
        "event_type": req.event_type,
        "event_data": req.event_data
    }
    
    db.table("raw_customer_touchpoints").insert(touchpoint_data).execute()
    
    # Trigger Identity Stitching Agent on the fly
    agent = IdentityStitchingAgent()
    result = agent.run(req.email)
    
    return {
        "message": "Touchpoint ingested and identity stitching completed.",
        "profiling_details": result
    }

@app.get("/api/stream-campaign")
def stream_campaign(email: str):
    """
    Initiates the Agentic Supply Chain and streams logs & outputs via Server-Sent Events (SSE).
    """
    orchestrator = CampaignOrchestrator()
    return StreamingResponse(
        orchestrator.execute(email),
        media_type="text/event-stream"
    )

@app.post("/api/reset-db")
def reset_database():
    db = get_db()
    if hasattr(db, 'seed_data'):
        db.seed_data()
        return {"status": "success", "message": "In-memory database reset & seeded successfully."}
    else:
        # For real Supabase, you would run the seed SQL via a function or query
        try:
            db.rpc("insert_mock_data").execute()
            return {"status": "success", "message": "Supabase database seeded successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to seed Supabase: {str(e)}")

# Serve frontend build in production
from fastapi.staticfiles import StaticFiles
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
else:
    print(f"Frontend dist folder not found at {frontend_dist}. Running in API-only mode.")

