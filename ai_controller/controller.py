import asyncio
import websockets
import json
import os
import re
import google.generativeai as genai
from . import prompt_builder # Import the prompt builder

class BlenderController:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.request_id = 0
        self.responses = {}

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        print("✅ Connected to Blender Nexus.")

    async def _send_request(self, method, params={}):
        self.request_id += 1
        request = {"jsonrpc": "2.0", "method": method, "params": params, "id": self.request_id}
        await self.websocket.send(json.dumps(request))
        
        # Wait for the response
        while self.request_id not in self.responses:
            await asyncio.sleep(0.1)
        return self.responses.pop(self.request_id)

    async def listen(self):
        """Listens for incoming messages and stores them."""
        while True:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                if "id" in data:
                    self.responses[data["id"]] = data
            except websockets.exceptions.ConnectionClosed:
                print("Connection to Blender lost.")
                break

    async def get_scene_objects(self):
        response = await self._send_request("list_scene_objects")
        return response.get("result", {}).get("data")

    async def get_object_details(self, name):
        response = await self._send_request("get_object_details", {"name": name})
        return response.get("result", {}).get("data")

    async def execute_plan(self, command_list):
        print(f"Executing plan with {len(command_list)} steps...")
        for i, command_json in enumerate(command_list):
            print(f"--- Step {i+1} ---")
            method = command_json.get("function")
            params = command_json.get("params", {})
            if method:
                print(f"▶️ Sending Action: {method} with params: {params}")
                response = await self._send_request(method, params)
                print(f"✅ Blender Response: {response.get('result', {}).get('message')}")
                await asyncio.sleep(0.5)
            else:
                print("Skipping invalid command step.")


async def main():
    try:
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        generation_config = {"response_mime_type": "application/json"}
        gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config=generation_config)
    except Exception as e:
        print(f"[FATAL ERROR] Failed to configure Gemini: {e}"); return

    controller = BlenderController("ws://localhost:8765")
    try:
        await controller.connect()
    except ConnectionRefusedError:
        print("[FATAL ERROR] Connection to Blender refused. Is Blender open and the server running?"); return
        
    # Start listening for responses in the background
    asyncio.create_task(controller.listen())

    print("\n--- Blender Nexus Controller (v1.0) ---")
    while True:
        # 1. SENSE
        scene_objects = await controller.get_scene_objects()
        
        # 2. THINK (Part 1)
        user_input = input("🎤 Your command: ")
        if user_input.lower() in ['exit', 'quit']: break
        
        # 3. SENSE (Part 2)
        scene_context = f"The scene contains: {scene_objects if scene_objects else 'nothing'}."
        mentioned_object = next((name for name in scene_objects if re.search(r'\b' + re.escape(name) + r'\b', user_input, re.IGNORECASE)), None)
        if mentioned_object:
            details = await controller.get_object_details(mentioned_object)
            if details: scene_context += f"\nCurrent details for '{mentioned_object}': {details}"
        
        # 4. THINK (Part 2)
        system_prompt = prompt_builder.get_system_prompt(scene_context)
        full_prompt = system_prompt + "\n\nUser Request: " + user_input
        print("🤔 Thinking with Gemini...")
        response = gemini_model.generate_content(full_prompt)
        ai_response = json.loads(response.text)
        print(f"DEBUG: Raw AI Response received: {ai_response}")

        # 5. ACT
        command_list = ai_response if isinstance(ai_response, list) else [ai_response]
        await controller.execute_plan(command_list)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting controller.")
        