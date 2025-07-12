# Blender Nexus: AI-Powered 3D Control Hub

Blender Nexus is an advanced, real-time control plane for Blender, enabling complex procedural generation and scene manipulation through an AI-driven, service-oriented architecture. It transforms Blender from a manual tool into a programmable 3D engine that can be directed by external AI logic.

This project is designed to showcase a professional software architecture, including real-time communication protocols, API-driven design, and third-party service integration.

## Key Technical Pillars

* **Service-Oriented Architecture:** The system is decoupled into two main components:
    * **The Blender "Execution Engine" Addon:** A robust server running inside Blender that exposes its core functionality.
    * **The AI "Logic Core" Controller:** An external Python application that handles user interaction, planning, and communication with AI services.
* **Real-Time Control via WebSockets:** Instead of basic HTTP, Nexus implements a persistent WebSocket connection. This provides a low-latency, bi-directional communication channel essential for real-time, interactive control and for receiving live updates from Blender.
* **API-Driven Design:** All communication follows a structured JSON-RPC protocol, ensuring reliability and making the platform easy to extend with new commands.
* **External Asset & API Integration:** The system is built to orchestrate multiple services, with commands for importing assets from URLs and interfacing with the Google Gemini LLM for complex task planning.

## Features

-   **Natural Language Control:** Use plain English to direct actions in Blender.
-   **Scene Awareness:** The AI fetches the current state of the scene (objects, transforms, modifiers) to make informed, contextual decisions.
-   **Procedural Execution:** Handles complex, multi-step commands (e.g., "create a sphere, add a bevel modifier, and color it red") by breaking them down into a sequence of actions.
-   **Advanced Capabilities:** Supports creating primitives, all major transformations, material properties (color, metallic, roughness), common modifiers (Bevel, Subsurf, Array), and importing of external `.glb` models.

## Setup

1.  **Blender:** Install the `blender_addon` folder as a standard Blender addon and enable it.
2.  **Controller:** In a separate terminal, create a Python virtual environment and install dependencies: `pip install -r requirements.txt`.
3.  **API Key:** Set the `GOOGLE_API_KEY` environment variable.
4.  **Run:** Start the server from the panel in Blender's 3D View, then run `python ai_controller/controller.py`.