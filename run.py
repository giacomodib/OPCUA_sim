# run.py
import asyncio
import threading
from api.app import app
from backend.opcua_server import main as opcua_main

def run_opcua_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(opcua_main())

def run_flask():
    app.run(debug=True, use_reloader=False, threaded=True)

if __name__ == "__main__":
    # Start OPC UA server in a separate thread
    opcua_thread = threading.Thread(target=run_opcua_server)
    opcua_thread.daemon = True
    opcua_thread.start()

    # Start Flask in the main thread
    run_flask()