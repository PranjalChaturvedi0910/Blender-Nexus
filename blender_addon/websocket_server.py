import asyncio
import websockets
import threading
import json
import bpy
from . import command_handler

# --- Global state for the server and thread ---
server_instance = None
server_thread = None

# --- Main WebSocket handler ---
async def handler(websocket, path):
    """Handles incoming messages from the AI controller."""
    print("Blender Nexus: Client connected.")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                # Assume JSON-RPC format: {"method": "...", "params": {...}, "id": ...}
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")

                if method:
                    # Schedule the command to run in Blender's main thread
                    bpy.app.timers.register(lambda: command_handler.execute_command(method, params, websocket, request_id))
                else:
                    await websocket.send(json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": request_id}))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}))
            except Exception as e:
                print(f"Error during message handling: {e}")
                await websocket.send(json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": f"Server error: {e}"}}))
    except websockets.exceptions.ConnectionClosed:
        print("Blender Nexus: Client disconnected.")
    finally:
        print("Blender Nexus: Connection handler finished.")

# --- Server start/stop logic ---
def run_server_loop(loop, server):
    """Function to run the asyncio event loop."""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server)
    loop.run_forever()

def start_server():
    """Starts the WebSocket server in a separate thread."""
    global server_instance, server_thread
    if server_thread is None or not server_thread.is_alive():
        loop = asyncio.new_event_loop()
        start_server_coro = websockets.serve(handler, "localhost", 8765, loop=loop)
        server_instance = loop.run_until_complete(start_server_coro)
        
        server_thread = threading.Thread(target=run_server_loop, args=(loop, server_instance))
        server_thread.daemon = True
        server_thread.start()
        print("Blender Nexus WebSocket server started on ws://localhost:8765")

def stop_server():
    """Stops the WebSocket server."""
    global server_instance, server_thread
    if server_instance:
        print("Blender Nexus: Stopping server...")
        loop = server_instance.get_loop()
        loop.call_soon_threadsafe(server_instance.close)
        loop.call_soon_threadsafe(loop.stop)
        server_thread.join(timeout=1)
        server_instance = None
        server_thread = None
        print("Blender Nexus: Server stopped.")

def is_server_running():
    """Checks if the server thread is active."""
    return server_thread is not None and server_thread.is_alive()