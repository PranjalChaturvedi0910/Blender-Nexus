import bpy
import json
import math
import tempfile
import os
import urllib.request
import asyncio

# --- Color Name to Value Mapping ---
COLOR_MAP = {"RED": (1,0,0,1), "GREEN": (0,1,0,1), "BLUE": (0,0,1,1), "WHITE": (1,1,1,1), "BLACK": (0,0,0,1), "YELLOW": (1,1,0,1), "ORANGE": (1,0.5,0,1), "PURPLE": (0.5,0,0.5,1), "CYAN": (0,1,1,1), "MAGENTA":(1,0,1,1), "LIME": (0.5,1,0,1), "PINK": (1,0.75,0.8,1), "BROWN": (0.6,0.4,0.2,1), "NAVY": (0,0,0.5,1), "TEAL": (0,0.5,0.5,1), "SILVER": (0.75,0.75,0.75,1), "GRAY": (0.5,0.5,0.5,1)}

# --- Helper Functions ---
def parse_vector(value, default=(0,0,0)):
    # (Same robust parse_vector function from before)
    if isinstance(value, (list, tuple)) and len(value) == 3: return tuple(float(v) for v in value)
    if isinstance(value, str):
        try:
            parts = value.replace('(', '').replace(')', '').split(',')
            if len(parts) == 3: return tuple(float(p.strip()) for p in parts)
        except (ValueError, TypeError): return default
    return default

# --- Command Implementations ---
def create_primitive(params):
    shape = params.get('shape', 'CUBE').upper()
    size_input, size = params.get('size'), 1.0
    if isinstance(size_input, (int, float)): size = float(size_input)
    elif isinstance(size_input, (list, tuple)) and size_input: size = float(size_input[0])
    location = parse_vector(params.get('location'), default=(0.0, 0.0, 0.0))
    if shape == 'CUBE': bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    elif shape == 'SPHERE': bpy.ops.mesh.primitive_uv_sphere_add(radius=size/2, location=location)
    # ... Add other shapes here if desired ...
    return {"status": "success", "message": f"{shape.title()} created."}

def move_object(params):
    obj = bpy.data.objects.get(params.get('name'))
    if obj: obj.location = parse_vector(params.get('location'), default=obj.location)
    return {"status": "success", "message": f"Moved {obj.name}."}

def set_object_color(params):
    obj, color_input = bpy.data.objects.get(params.get('name')), params.get('color')
    if not obj: return {"status": "error", "message": "Object not found."}
    # ... (Same robust color logic from before) ...
    final_color = (1.0, 1.0, 1.0, 1.0)
    if isinstance(color_input, list): final_color = tuple(color_input)
    elif isinstance(color_input, str):
        if color_input.strip().startswith('['):
            try: final_color = tuple(json.loads(color_input.replace("'", "\"")))
            except Exception: pass
        else: final_color = COLOR_MAP.get(color_input.upper(), final_color)
    if len(final_color) == 3: final_color += (1.0,)
    obj.color = final_color
    if not obj.data.materials: obj.data.materials.append(bpy.data.materials.new(name=f"{obj.name}_Mat"))
    mat = obj.active_material if obj.active_material else obj.material_slots[0].material
    mat.diffuse_color = final_color
    if mat.use_nodes and mat.node_tree.nodes.get('Principled BSDF'): mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = final_color
    return {"status": "success", "message": f"Set color for {obj.name}."}
    
def import_asset(params):
    url = params.get('url')
    if not url: return {"status": "error", "message": "URL parameter is missing."}
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp_file:
            tmp_file.write(response.read())
            filepath = tmp_file.name
    bpy.ops.import_scene.gltf(filepath=filepath)
    os.remove(filepath)
    return {"status": "success", "message": f"Imported asset from {url}."}

# --- Getter Commands (run immediately) ---
def list_scene_objects(params):
    return {"status": "success", "data": [o.name for o in bpy.data.objects if o.type in ('MESH', 'LIGHT', 'CAMERA')]}
def get_object_details(params):
    obj = bpy.data.objects.get(params.get('name'))
    if obj: return {"status": "success", "data": {'name': obj.name, 'location': list(obj.location), 'rotation_degrees': [math.degrees(a) for a in obj.rotation_euler], 'scale': list(obj.scale), 'modifiers': [m.name for m in obj.modifiers]}}
    else: return {"status": "error", "message": "Object not found."}

# --- Command Dispatcher ---
COMMANDS = {
    "create_primitive": create_primitive, "move_object": move_object,
    "set_object_color": set_object_color, "import_asset": import_asset,
    # Add other action commands here...
}
GETTER_COMMANDS = {
    "list_scene_objects": list_scene_objects,
    "get_object_details": get_object_details,
}

def execute_command(method, params, websocket, request_id):
    """The main function scheduled by the timer to run commands in Blender's main thread."""
    result_data = None
    try:
        if method in COMMANDS:
            result_data = COMMANDS[method](params)
        elif method in GETTER_COMMANDS:
            result_data = GETTER_COMMANDS[method](params)
        else:
            result_data = {"status": "error", "message": "Method not found"}
        
        # Formulate response
        response = {"jsonrpc": "2.0", "result": result_data, "id": request_id}
    except Exception as e:
        print(f"Error executing command '{method}': {e}")
        response = {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": request_id}
    
    # Send response back over WebSocket
    asyncio.run_coroutine_threadsafe(websocket.send(json.dumps(response)), websocket.loop)
    return None # Important for bpy.app.timers