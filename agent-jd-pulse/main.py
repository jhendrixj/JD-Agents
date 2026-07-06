from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.ingest import get_full_artist_profile
from models.analytics import run_full_analytics
from reports.generator import generate_report


# ─────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────

app = FastAPI(
    title="Agent JD: Pulse",
    description="Music Intelligence Agent — The JD Agent Suite",
    version="1.0.0"
)


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────

class PulseRequest(BaseModel):
    artist_name: str
    order_id: str = None
    tier: str = "basic"  # basic, pro, forecast


class PulseResponse(BaseModel):
    order_id: str
    artist_name: str
    status: str
    report_path: str = None
    generated_at: str = None
    message: str = None


# ─────────────────────────────────────────
# ORDER STORAGE (in-memory for MVP)
# ─────────────────────────────────────────

orders = {}


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.get("/")
def root():
    return {
        "agent": "Agent JD: Pulse",
        "suite": "The JD Agent Suite",
        "version": "1.0.0",
        "status": "online",
        "description": "Music intelligence and analytics for independent artists",
        "tiers": {
            "basic": "Streaming analytics and audience report — $15",
            "pro": "Full report including social, revenue gaps, and benchmarking — $35",
            "forecast": "Pro + predictive release timing and growth projection — $65"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent": "Agent JD: Pulse"
    }


@app.post("/order", response_model=PulseResponse)
async def create_order(request: PulseRequest, background_tasks: BackgroundTasks):
    """
    Receives an order for a music intelligence report.
    Processes the request and generates a PDF report.
    """

    # Generate order ID if not provided
    order_id = request.order_id or str(uuid.uuid4())

    # Store order as pending
    orders[order_id] = {
        "order_id": order_id,
        "artist_name": request.artist_name,
        "tier": request.tier,
        "status": "processing",
        "created_at": datetime.now().isoformat()
    }

    # Process in background
    background_tasks.add_task(
        process_order,
        order_id,
        request.artist_name,
        request.tier
    )

    return PulseResponse(
        order_id=order_id,
        artist_name=request.artist_name,
        status="processing",
        message=f"Order received. Report for {request.artist_name} is being generated."
    )


async def process_order(order_id: str, artist_name: str, tier: str):
    """
    Background task that runs the full pipeline:
    1. Fetch artist data
    2. Run analytics
    3. Generate PDF report
    4. Update order status
    """
    try:
        print(f"\nProcessing order {order_id} for {artist_name}...")

        # Step 1 — Fetch data
        print("Fetching artist data...")
        profile = get_full_artist_profile(artist_name)

        if "error" in profile:
            orders[order_id]["status"] = "failed"
            orders[order_id]["error"] = profile["error"]
            return

        # Step 2 — Run analytics
        print("Running analytics...")
        analytics = run_full_analytics(profile)

        # Step 3 — Generate report
        print("Generating report...")
        report_path = generate_report(analytics)

        # Step 4 — Update order
        orders[order_id]["status"] = "completed"
        orders[order_id]["report_path"] = report_path
        orders[order_id]["completed_at"] = datetime.now().isoformat()

        print(f"Order {order_id} completed. Report at: {report_path}")

    except Exception as e:
        orders[order_id]["status"] = "failed"
        orders[order_id]["error"] = str(e)
        print(f"Order {order_id} failed: {str(e)}")


@app.get("/order/{order_id}")
def get_order_status(order_id: str):
    """
    Check the status of an order.
    """
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    return orders[order_id]


@app.get("/order/{order_id}/download")
def download_report(order_id: str):
    """
    Download the generated PDF report for a completed order.
    """
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")

    order = orders[order_id]

    if order["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not ready. Current status: {order['status']}"
        )

    report_path = order.get("report_path")

    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=os.path.basename(report_path)
    )


@app.get("/orders")
def list_orders():
    """
    List all orders — for monitoring purposes.
    """
    return {
        "total_orders": len(orders),
        "orders": list(orders.values())
    }


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)