import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for Falcon AI application"""
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-development-secret-key-123')
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    
    # MongoDB Configuration
    # Flask-PyMongo expects MONGO_URI specifically, so set both for clarity.
    MONGO_URI = os.environ.get('MONGO_URI') or os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/falcon_ai'
    MONGODB_URI = MONGO_URI
    MONGODB_DB = 'falcon_ai'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # YOLO Model Configuration
    MODEL_PATH = os.environ.get('MODEL_PATH') or os.path.join(BASE_DIR, "New_Model", "MODEL_FILE", "best.pt")
    DEFAULT_SOURCE = os.environ.get('DEFAULT_SOURCE') or os.path.join(BASE_DIR, "New_Model", "IN_OUT_VIDEO", "16.mp4")
    CONF = 0.35
    
    # Fence handling config
    USE_AUTO_FENCE = True
    FENCE_EDGE = "bottom"
    FENCE_SMOOTH_ALPHA = 0.20
    FENCE_HOLD_IF_MISSED = 25
    FALLBACK_LINE_Y = 215
    BAND_PX = 100
    
    # Alert policy config
    REQUIRE_CROSSING = True
    ALERT_COOLDOWN_S = 45
    MIN_STAY_FRAMES = 6
    ONSCREEN_DIR_FRAMES = 35
    
    # Side labels for alerts
    SIDE_TOP = "Secure Zone"
    SIDE_BOTTOM = "Border Zone"
    PUSHIN_LABEL = f"{SIDE_TOP} -> {SIDE_BOTTOM} (PUSH-IN)"
    PUSHOUT_LABEL = f"{SIDE_BOTTOM} -> {SIDE_TOP} (PUSH-OUT)"
    
    # Twilio Configuration
    TWILIO_SID = os.environ.get("TWILIO_SID")
    TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
    FROM_NUMBER = os.environ.get("FROM_NUMBER")
    TO_NUMBER = os.environ.get("TO_NUMBER")
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Ensure upload folder exists
    @staticmethod
    def init_app(app):
        os.makedirs(Config.get_upload_path(), exist_ok=True)

    @staticmethod
    def get_upload_path(filename: str | None = None):
        """Return absolute path inside static/uploads (creates if needed)."""
        upload_dir = os.path.join(Config.BASE_DIR, Config.UPLOAD_FOLDER)
        os.makedirs(upload_dir, exist_ok=True)
        if filename:
            return os.path.join(upload_dir, filename)
        return upload_dir

