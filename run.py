import asyncio
import threading
from api.app import app
from backend.opcua_server import main as opcua_main


def run_opcua_server():
    """Run the OPC UA server in its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(opcua_main())
    loop.close()

def run_flask():
    """Run the Flask application"""
    app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=True
        )


if __name__ == "__main__":
    opcua_thread = threading.Thread(target=run_opcua_server)
    opcua_thread.daemon = True
    opcua_thread.start()

    run_flask()