"""
Configuración general del proyecto.

Todas las variables importantes se leen desde Railway
o desde el archivo .env cuando trabajamos localmente.
"""

import os

from dotenv import load_dotenv

# Cargar variables del archivo .env (solo en desarrollo local)
load_dotenv()

# ==========================================================
# TYPEBOT
# ==========================================================

TYPEBOT_API_TOKEN = os.getenv("TYPEBOT_API_TOKEN")
TYPEBOT_PUBLIC_ID = os.getenv("TYPEBOT_PUBLIC_ID")

# ==========================================================
# WHATSAPP (Meta)
# ==========================================================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# ==========================================================
# OPENAI (para el futuro)
# ==========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")