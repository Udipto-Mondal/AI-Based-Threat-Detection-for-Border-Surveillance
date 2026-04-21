"""
Legacy entry-point preserved for compatibility.
The heavy lifting now lives inside the falcon_ai package.
"""
import os

from falcon_ai import create_app
from falcon_ai.app.core import load_model, start_processing_thread
from falcon_ai.config import Config


app = create_app(Config)


def _boot_detection():
    """Load model and spin up the background analysis thread."""
    if load_model():
        start_processing_thread(Config.DEFAULT_SOURCE)
    else:
        print("⚠️ YOLO model failed to load. Start analysis via dashboard once fixed.")

# Boot background detection if running via a WSGI server or without flask auto-reloader
if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    _boot_detection()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    print("=" * 72)
    print("🦅 FALCON AI - BORDER DEFENSE SYSTEM (Modular Architecture)")
    print("=" * 72)
    print(f"📡 MongoDB URI: {Config.MONGO_URI}")
    print(f"📁 Uploads Directory: {os.path.abspath(Config.get_upload_path())}")
    print("=" * 72)
    _boot_detection()
    app.run(host=host, port=port, debug=debug_mode, threaded=True)
    print(f"🚀 Application started on http://{host}:{port}")
    print(f"🔐 Login at http://{host}:{port}/auth/login")
    print(f"🔐 Register at http://{host}:{port}/auth/register")
    print("=" * 72)
    