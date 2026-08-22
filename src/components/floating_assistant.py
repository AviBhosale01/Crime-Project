"""
Floating 3D Police Assistant Widget Component
"""
import streamlit as st
import os
import base64

def render_floating_assistant(selected_page: str):
    """
    Render the fixed viewport-docked 3D police assistant icon with instant 1-click chatbot navigation.
    """
    police_icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "police-3d-icon.png")
    police_icon_b64 = ""
    if os.path.exists(police_icon_path):
        with open(police_icon_path, "rb") as img_f:
            police_icon_b64 = base64.b64encode(img_f.read()).decode("utf-8")

    if police_icon_b64 and selected_page != "💬 AI Intel Chatbot":
        st.markdown(f"""
        <style>
        #floating-police-assistant-wrapper {{
            position: fixed !important;
            bottom: 22px !important;
            right: 22px !important;
            z-index: 2147483647 !important;
            display: block !important;
            text-decoration: none !important;
        }}
        
        #floating-police-assistant-btn {{
            position: relative !important;
            width: 52px !important;
            height: 52px !important;
            border-radius: 50% !important;
            background: radial-gradient(circle at 35% 35%, #1e40af, #0f172a) !important;
            border: 2px solid #60a5fa !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6), 0 0 15px rgba(59, 130, 246, 0.45) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease, border-color 0.25s ease !important;
            text-decoration: none !important;
        }}
        
        #floating-police-assistant-btn:hover {{
            transform: scale(1.12) translateY(-3px) !important;
            border-color: #93c5fd !important;
            box-shadow: 0 10px 28px rgba(37, 99, 235, 0.85), 0 0 22px rgba(96, 165, 250, 0.7) !important;
        }}
        
        #floating-police-assistant-img {{
            width: 38px !important;
            height: 38px !important;
            object-fit: contain !important;
            pointer-events: none !important;
            filter: drop-shadow(0 3px 6px rgba(0, 0, 0, 0.45)) !important;
        }}
        
        #floating-ai-badge {{
            position: absolute !important;
            top: -3px !important;
            right: -3px !important;
            background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            color: #ffffff !important;
            font-size: 0.55rem !important;
            font-weight: 800 !important;
            font-family: 'Outfit', sans-serif !important;
            padding: 1px 5px !important;
            border-radius: 8px !important;
            border: 1.5px solid #1e293b !important;
            box-shadow: 0 2px 5px rgba(239, 68, 68, 0.6) !important;
            letter-spacing: 0.5px !important;
        }}

        @keyframes pulse-ring {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.18); opacity: 0; }}
            100% {{ transform: scale(0.95); opacity: 0; }}
        }}
        
        .floating-pulse-aura {{
            position: absolute !important;
            width: 100% !important;
            height: 100% !important;
            border-radius: 50% !important;
            border: 2px solid rgba(96, 165, 250, 0.6) !important;
            animation: pulse-ring 2.5s infinite ease-out !important;
            pointer-events: none !important;
        }}
        </style>
        
        <div id="floating-police-assistant-wrapper">
            <a href="?page=chatbot" target="_self" id="floating-police-assistant-btn" title="Open AI Intel Assistant Chatbot">
                <div class="floating-pulse-aura"></div>
                <img id="floating-police-assistant-img" src="data:image/png;base64,{police_icon_b64}" alt="AI Intel Officer" />
                <span id="floating-ai-badge">AI</span>
            </a>
        </div>
        """, unsafe_allow_html=True)
