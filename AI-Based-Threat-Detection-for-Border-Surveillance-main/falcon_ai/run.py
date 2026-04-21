"""
Entry point for Falcon AI Border Defense System
"""
from app import create_app
from config import Config

app = create_app(Config)

if __name__ == '__main__':
    print("=" * 60)
    print("🦅 FALCON AI - BORDER DEFENSE SYSTEM (Modular Architecture)")
    print("=" * 60)
    print("📡 MongoDB URI:", Config.MONGODB_URI)
    print("🔐 Secret Key:", "***" if Config.SECRET_KEY else "NOT SET")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)

