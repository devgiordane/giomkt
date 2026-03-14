import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/giomkt.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "default")
FB_APP_ID = os.getenv("FB_APP_ID", "")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")
FEATURE_FACEBOOK = os.getenv("FEATURE_FACEBOOK", "false").lower() == "true"
EDUZZ_API_URL = os.getenv("EDUZZ_API_URL", "https://api.eduzz.com")
EDUZZ_CLIENT_ID = os.getenv("EDUZZ_CLIENT_ID", "eb5e2be8-bd64-4f52-8fce-1cbc70bc596c")
EDUZZ_CLIENT_SECRET = os.getenv("EDUZZ_CLIENT_SECRET", "28397f6c83fc2569fdd720c459c01350731b160d7e8cb39085f0b6b6cfbb5114")
EDUZZ_REDIRECT_URI = os.getenv("EDUZZ_REDIRECT_URI", "https://dash.my.adm.br/api/eduzz/callback")
UMAMI_API_URL = os.getenv("UMAMI_API_URL", "")
UMAMI_API_TOKEN = os.getenv("UMAMI_API_TOKEN", "")
