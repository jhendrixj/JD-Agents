from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from epk.generator import generate_epk

# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

app = FastAPI(
    title="Agent JD: Press",
    description="EPK Generator Agent — The JD Agent Suite",
    version="1.0.0"
)

# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class PressRequest(BaseModel):
    artist_name: str
    genre: str = ""
    bio: str = ""
    achievements: str = ""
    social_links: dict = {}
    contact_email: str = ""
    order_id: str = None
    # A2A fields — populated when called by Agent JD: Pulse
    pulse_data: dict = {}


class PressResponse(BaseModel):
    order_id: str
    artist_name: str
    status: str
    report_path: str = None
    generated_at: str = None
    message: str = None


# ─────────────────────────────────────────
# ORDER STORAGE
# ─────────────────────────────────────────

orders = {}


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "agent": "Agent JD: Press",
        "suite": "The JD Agent Suite",
        "version": "1.0.0",
        "status": "online",
        "description": "Electronic Press Kit generator for independent artists",
        "pricing": {
            "basic_epk": "Artist bio, one-pager, and media talking points — $20",
            "full_epk": "Full EPK including bio, one-pager, talking points, and booking rider — $35"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent": "Agent JD: Press"
    }


@app.post("/order", response_model=PressResponse)
async def create_order(request: PressRequest, background_tasks: BackgroundTasks):
    """
    Receives an order for an EPK.
    Can be called by a human buyer or by Agent JD: Pulse (A2A).
    """
    order_id = request.order_id or str(uuid.uuid4())

    orders[order_id] = {
        "order_id": order_id,
        "artist_name": request.artist_name,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }

    background_tasks.add_task(
        process_order,
        order_id,
        request
    )

    return PressResponse(
        order_id=order_id,
        artist_name=request.artist_name,
        status="processing",
        message=f"EPK for {request.artist_name} is being generated."
    )


async def process_order(order_id: str, request: PressRequest):
    """
    Background task that generates the EPK.
    """
    try:
        print(f"\nProcessing EPK order {order_id} for {request.artist_name}...")

        epk_path = generate_epk(
            artist_name=request.artist_name,
            genre=request.genre,
            bio=request.bio,
            achievements=request.achievements,
            social_links=request.social_links,
            contact_email=request.contact_email,
            pulse_data=request.pulse_data
        )

        orders[order_id]["status"] = "completed"
        orders[order_id]["report_path"] = epk_path
        orders[order_id]["completed_at"] = datetime.now().isoformat()

        print(f"EPK order {order_id} completed. File at: {epk_path}")

    except Exception as e:
        orders[order_id]["status"] = "failed"
        orders[order_id]["error"] = str(e)
        print(f"EPK order {order_id} failed: {str(e)}")


@app.get("/order/{order_id}")
def get_order_status(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders[order_id]


@app.get("/order/{order_id}/download")
def download_epk(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"EPK not ready. Current status: {order['status']}"
        )

    epk_path = order.get("report_path")

    if not epk_path or not os.path.exists(epk_path):
        raise HTTPException(status_code=404, detail="EPK file not found")

    return FileResponse(
        path=epk_path,
        media_type="application/pdf",
        filename=os.path.basename(epk_path)
    )


@app.get("/orders")
def list_orders():
    return {
        "total_orders": len(orders),
        "orders": list(orders.values())
    }


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)