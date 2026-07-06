import asyncio
import os
import json
import sys
from dotenv import load_dotenv
from croo import AgentClient, Config, EventType, DeliverableType, DeliverOrderRequest, APIError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.ingest import get_full_artist_profile
from models.analytics import run_full_analytics
from reports.generator import generate_report

# Load environment variables
load_dotenv()


# ─────────────────────────────────────────
# CROO CLIENT SETUP
# ─────────────────────────────────────────

def get_croo_client():
    config = Config(
        base_url=os.environ["CROO_API_URL"],
        ws_url=os.environ["CROO_WS_URL"],
    )
    sdk_key = os.environ.get("CROO_SDK_KEY") or os.environ.get("CROO_API_KEY")
    return AgentClient(config, sdk_key)


# ─────────────────────────────────────────
# ORDER PROCESSOR
# ─────────────────────────────────────────

async def process_croo_order(client: AgentClient, order_id: str, requirements: str):
    """
    Processes a CROO order end to end:
    1. Parse requirements
    2. Fetch artist data
    3. Run analytics
    4. Generate PDF report
    5. Upload report to CROO file storage
    6. Deliver download URL to buyer
    """
    try:
        print(f"\nProcessing CROO order: {order_id}")

        # Step 1 — Parse requirements
        try:
            req = json.loads(requirements)
            artist_name = req.get("artist_name", "").strip()
            tier = req.get("tier", "basic").strip().lower()
        except json.JSONDecodeError:
            # If not JSON, treat the whole string as artist name
            artist_name = requirements.strip()
            tier = "basic"

        if not artist_name:
            await client.deliver_order(order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps({
                    "status": "error",
                    "message": "No artist name provided. Please include artist_name in your request."
                })
            ))
            return

        print(f"Artist: {artist_name} | Tier: {tier}")

        # Step 2 — Fetch artist data
        print("Fetching artist data...")
        profile = get_full_artist_profile(artist_name)

        if "error" in profile:
            await client.deliver_order(order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps({
                    "status": "error",
                    "message": profile["error"]
                })
            ))
            return

        # Step 3 — Run analytics
        print("Running analytics...")
        analytics = run_full_analytics(profile)

        # Step 4 — Generate PDF report
        print("Generating PDF report...")
        report_path = generate_report(analytics)

        # Step 5 — Upload report to CROO file storage
        print("Uploading report to CROO...")
        report_filename = os.path.basename(report_path)

        with open(report_path, "rb") as f:
            report_bytes = f.read()

        object_key = await client.upload_file(report_filename, report_bytes)
        download_url = await client.get_download_url(object_key)

        print(f"Report uploaded. Download URL: {download_url}")

        # Step 6 — Deliver to buyer
        delivery_payload = {
            "status": "completed",
            "artist": artist_name,
            "tier": tier,
            "report_filename": report_filename,
            "download_url": download_url,
            "message": f"Your music intelligence report for {artist_name} is ready.",
            "generated_by": "Agent JD: Pulse | The JD Agent Suite"
        }

        await client.deliver_order(order_id, DeliverOrderRequest(
            deliverable_type=DeliverableType.TEXT,
            deliverable_text=json.dumps(delivery_payload)
        ))

        print(f"Order {order_id} delivered successfully!")

    except APIError as e:
        print(f"CROO API Error on order {order_id}: {e.code} — {e.reason}")
    except Exception as e:
        print(f"Unexpected error on order {order_id}: {str(e)}")
        try:
            await client.deliver_order(order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps({
                    "status": "error",
                    "message": "An unexpected error occurred. Please try again."
                })
            ))
        except Exception:
            pass


# ─────────────────────────────────────────
# MAIN PROVIDER LOOP
# ─────────────────────────────────────────

async def run_provider():
    """
    Main provider loop — connects to CROO via WebSocket,
    listens for incoming orders, and processes them.
    """
    print("\n" + "="*50)
    print("  Agent JD: Pulse — CROO Provider")
    print("  The JD Agent Suite")
    print("="*50)

    client = get_croo_client()

    print("\nConnecting to CROO network...")
    stream = await client.connect_websocket()
    print("Connected! Listening for orders...\n")

    # ── Handle incoming negotiations ──
    def on_negotiation(e):
        async def _handle():
            try:
                print(f"New negotiation received: {e.negotiation_id}")
                result = await client.accept_negotiation(e.negotiation_id)
                print(f"Negotiation accepted. Order created: {result.order.order_id}")
            except APIError as err:
                print(f"Failed to accept negotiation {e.negotiation_id}: {err}")
        asyncio.create_task(_handle())

    # ── Handle paid orders ──
    def on_paid(e):
        async def _handle():
            print(f"Payment confirmed for order: {e.order_id}")
            # Get order details to retrieve requirements
            try:
                order = await client.get_order(e.order_id)
                requirements = order.order.requirements or "{}"
                await process_croo_order(client, e.order_id, requirements)
            except APIError as err:
                print(f"Failed to retrieve order {e.order_id}: {err}")
        asyncio.create_task(_handle())

    # ── Handle rejected negotiations ──
    def on_rejected(e):
        print(f"Negotiation rejected: {e.negotiation_id}")

    # ── Handle expired orders ──
    def on_expired(e):
        print(f"Order expired: {e.order_id}")

    # Register event handlers
    stream.on(EventType.NEGOTIATION_CREATED, on_negotiation)
    stream.on(EventType.ORDER_PAID, on_paid)
    stream.on(EventType.NEGOTIATION_REJECTED, on_rejected)
    stream.on(EventType.ORDER_EXPIRED, on_expired)

    print("Agent JD: Pulse is live and ready to accept orders.")
    print("Press Ctrl+C to stop.\n")

    # Keep running until interrupted
    try:
        stop = asyncio.Event()
        await stop.wait()
    except KeyboardInterrupt:
        print("\nShutting down Agent JD: Pulse...")
        await stream.close()


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_provider())