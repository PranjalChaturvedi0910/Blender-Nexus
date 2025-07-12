import bpy
import threading
from . import websocket_server

bl_info = {
    "name": "Blender Nexus - AI Control Server",
    "author": "You",
    "version": (1, 0, "Professional"),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Nexus AI",
    "description": "Starts a WebSocket server for real-time AI control.",
    "category": "Development",
}

class NEXUS_OT_StartServer(bpy.types.Operator):
    bl_idname = "nexus.start_server"
    bl_label = "Start AI Server"
    def execute(self, context):
        websocket_server.start_server()
        self.report({'INFO'}, "Blender Nexus server started.")
        return {'FINISHED'}

class NEXUS_OT_StopServer(bpy.types.Operator):
    bl_idname = "nexus.stop_server"
    bl_label = "Stop AI Server"
    def execute(self, context):
        websocket_server.stop_server()
        self.report({'INFO'}, "Blender Nexus server stopped.")
        return {'FINISHED'}

class NEXUS_PT_Panel(bpy.types.Panel):
    bl_label = "Blender Nexus"; bl_idname = "NEXUS_PT_Panel"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = 'Nexus AI'
    def draw(self, context):
        layout = self.layout
        if websocket_server.is_server_running():
            layout.operator("nexus.stop_server", text="Stop Server", icon='CANCEL')
        else:
            layout.operator("nexus.start_server", text="Start Server", icon='PLAY')

classes = (NEXUS_OT_StartServer, NEXUS_OT_StopServer, NEXUS_PT_Panel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    websocket_server.stop_server()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)