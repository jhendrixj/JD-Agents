import asyncio
import os
import json
import sys
from dotenv import load_dotenv
from croo import AgentClient, Config, EventType, DeliverableType, DeliverOrderRequest, APIError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epk.generator import generate_epk

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
    Processes a CROO order for Agent JD: Press.
    1. Parse requirements
    2. Generate EPK
    3. Upload to CROO file storage
    4. Deliver download URL to buyer
    """
    try:
        print(f"\nProcessing CROO Press order: {order_id}")

        # Step 1 — Parse requirements
        try:
            req = json.loads(requirements)
            artist_name = req.get("artist_name", "").strip()
            genre = req.get("genre", "").strip()
            bio = req.get("bio", "").strip()
            contact_email = req.get("contact_email", "").strip()
        except json.JSONDecodeError:
            artist_name = requirements.strip()
            genre = ""
            bio = ""
            contact_email = ""

        if not artist_name:
            await client.deliver_order(order_id, DeliverOrderRequest(
                deliverable_type=DeliverableType.TEXT,
                deliverable_text=json.dumps({
                    "status": "error",
                    "message": "No artist name provided. Please include artist_name in your request."
                })
            ))
            return

        print(f"Generating EPK for: {artist_name}")

        # Step 2 — Try to pull Pulse data for richer EPK
        pulse_data = {}
        try:
            sys.path.append(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "..",
                    "agent-jd-pulse"
                )
            )
            from data.ingest import get_full_artist_profile
            print("Pulling artist data from Agent JD: Pulse pipeline...")
            pulse_data = get_full_artist_profile(artist_name)
        except Exception as e:
            print(f"Could not pull Pulse data: {str(e)} — proceeding with basic EPK")

        # Step 3 — Generate EPK
        print("Generating EPK...")
        epk_path = generate_epk(
            artist_name=artist_name,
            genre=genre,
            bio=bio,
            contact_email=contact_email,
            pulse_data=pulse_data
        )

        # Step 4 — Upload to CROO file storage
        print("Uploading EPK to CROO...")
        epk_filename = os.path.basename(epk_path)

        with open(epk_path, "rb") as f:
            epk_bytes = f.read()

        object_key = await client.upload_file(epk_filename, epk_bytes)
        download_url = await client.get_download_url(object_key)

        print(f"EPK uploaded. Download URL: {download_url}")

        # Step 5 — Deliver to buyer
        delivery_payload = {
            "status": "completed",
            "artist": artist_name,
            "epk_filename": epk_filename,
            "download_url": download_url,
            "message": f"Your Electronic Press Kit for {artist_name} is ready.",
            "generated_by": "Agent JD: Press | The JD Agent Suite"
        }

        await client.deliver_order(order_id, DeliverOrderRequest(
            deliverable_type=DeliverableType.TEXT,
            deliverable_text=json.dumps(delivery_payload)
        ))

        print(f"Press order {order_id} delivered successfully!")

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
    Main provider loop for Agent JD: Press.
    Connects to CROO via WebSocket and listens for orders.
    """
    print("\n" + "="*50)
    print("  Agent JD: Press — CROO Provider")
    print("  The JD Agent Suite")
    print("="*50)

    client = get_croo_client()

    print("\nConnecting to CROO network...")
    stream = await client.connect_websocket()
    print("Connected! Listening for EPK orders...\n")

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
            print(f"Payment confirmed for Press order: {e.order_id}")
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

    print("Agent JD: Press is live and ready to accept EPK orders.")
    print("Press Ctrl+C to stop.\n")

    try:
        stop = asyncio.Event()
        await stop.wait()
    except KeyboardInterrupt:
        print("\nShutting down Agent JD: Press...")
        await stream.close()


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_provider())