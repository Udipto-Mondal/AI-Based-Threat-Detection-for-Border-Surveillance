# Migration Guide: From Single File to Modular Architecture

This guide helps you transition from the old `app.py` single-file structure to the new modular architecture.

## Key Changes

### 1. Folder Structure
- **Old**: Single `app.py` file
- **New**: Modular structure with blueprints in `falcon_ai/app/`

### 2. Database
- **Old**: In-memory list (`alerts_storage`)
- **New**: MongoDB collections (`users`, `alerts`)

### 3. Authentication
- **Old**: No authentication
- **New**: User registration/login required

### 4. Routes
- **Old**: Direct routes in `app.py`
- **New**: Blueprint-based routes:
  - `/auth/login` - Login page
  - `/auth/register` - Registration page
  - `/dashboard` - Main dashboard (requires login)
  - `/analytics` - Analytics page (requires login)
  - `/api/chatbot/query` - Chatbot API (requires login)

## Migration Steps

### Step 1: Install New Dependencies

```bash
cd falcon_ai
pip install -r requirements.txt
```

New dependencies:
- `flask-pymongo` - MongoDB integration
- `flask-login` - Authentication
- `bcrypt` - Password hashing

### Step 2: Start MongoDB

Ensure MongoDB is running:

```bash
# Windows (if installed as service)
# Or start manually:
mongod

# Linux/Mac
sudo systemctl start mongod
```

### Step 3: Update Configuration

Edit `falcon_ai/config.py` to match your paths:
- `MODEL_PATH` - Your YOLO model location
- `DEFAULT_SOURCE` - Default video source
- `MONGODB_URI` - MongoDB connection (default: `mongodb://localhost:27017/falcon_ai`)

### Step 4: Run the New Application

```bash
cd falcon_ai
python run.py
```

### Step 5: Create Your First User

1. Navigate to `http://127.0.0.1:5000`
2. You'll be redirected to `/auth/login`
3. Click "Request Access" to register
4. Create your account
5. Log in

## Data Migration

### Alerts Data

If you have existing alerts in the old system, you can migrate them to MongoDB:

```python
# Migration script (run once)
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017')
db = client['falcon_ai']

# If you have old alerts_storage data, convert and insert:
# old_alerts = [...]  # Your old alerts list

# for alert in old_alerts:
#     db.alerts.insert_one({
#         'timestamp': datetime.strptime(alert['time'], "%Y-%m-%d %H:%M:%S"),
#         'frame_id': alert['frame'],
#         'track_id': alert['track_id'],
#         'type': alert['alert'],
#         'message': alert['message'],
#         'image_path': None
#     })
```

## Feature Comparison

| Feature | Old App | New App |
|---------|---------|---------|
| Video Processing | ✅ | ✅ |
| YOLO Detection | ✅ | ✅ |
| Alerts | In-memory list | MongoDB |
| Authentication | ❌ | ✅ |
| Analytics | Basic | Advanced with charts |
| Chatbot | ❌ | ✅ |
| User Management | ❌ | ✅ |
| Export Reports | Basic CSV | Enhanced CSV export |

## Breaking Changes

1. **Authentication Required**: All routes now require login (except `/auth/login` and `/auth/register`)
2. **Database**: Alerts are now stored in MongoDB, not in-memory
3. **Routes**: Some route paths have changed:
   - `/` → Redirects to login or dashboard
   - `/video_feed` → Still works, but requires login
   - `/api/status` → Still works, but requires login

## Troubleshooting

### "ModuleNotFoundError: No module named 'config'"
- Make sure you're running from the `falcon_ai/` directory
- Or set PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:/path/to/falcon_ai`

### "MongoDB Connection Error"
- Ensure MongoDB is running
- Check connection string in `config.py`
- Verify MongoDB is accessible on port 27017

### "Model Not Found"
- Update `MODEL_PATH` in `config.py`
- Ensure the model file exists

### Static Files Not Loading
- Ensure you're running from the `falcon_ai/` directory
- Check that `app/static/` folder exists with CSS/JS files

## Rollback

If you need to use the old version:
1. Keep your old `app.py` file
2. Run it directly: `python app.py`
3. The old version will continue to work independently

## Next Steps

1. ✅ Set up MongoDB
2. ✅ Install dependencies
3. ✅ Configure paths in `config.py`
4. ✅ Run the application
5. ✅ Create user account
6. ✅ Test video processing
7. ✅ Explore analytics dashboard
8. ✅ Try the chatbot

Enjoy your new modular architecture! 🚀

