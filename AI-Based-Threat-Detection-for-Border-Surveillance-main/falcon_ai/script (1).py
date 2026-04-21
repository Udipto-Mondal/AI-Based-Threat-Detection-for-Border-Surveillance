# 2. Requirements file for Flask backend
requirements = '''
flask==3.0.0
flask-cors==4.0.0
flask-socketio==5.3.6
ultralytics==8.2.0
opencv-python==4.8.1.78
numpy==1.24.3
twilio==8.10.0
python-socketio==5.11.0
'''

# 3. Updated server/routes/api.ts for your existing Express server to proxy to Flask
api_routes = '''
import { RequestHandler } from "express";
import { DemoResponse, AlertItem } from "@shared/api";
import fetch from 'node-fetch';

const FLASK_API_URL = 'http://localhost:5000/api';

export const handleDemo: RequestHandler = (req, res) => {
  const response: DemoResponse = {
    message: "Hello from Express server - Flask integration ready",
  };
  res.status(200).json(response);
};

// Proxy route to Flask backend for starting video processing
export const startProcessing: RequestHandler = async (req, res) => {
  try {
    const response = await fetch(`${FLASK_API_URL}/start_processing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to start processing' });
  }
};

// Proxy route for stopping video processing
export const stopProcessing: RequestHandler = async (req, res) => {
  try {
    const response = await fetch(`${FLASK_API_URL}/stop_processing`, {
      method: 'POST'
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to stop processing' });
  }
};

// Proxy route for getting alerts
export const getAlerts: RequestHandler = async (req, res) => {
  try {
    const response = await fetch(`${FLASK_API_URL}/alerts`);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get alerts' });
  }
};

// Proxy route for acknowledging alerts
export const acknowledgeAlert: RequestHandler = async (req, res) => {
  try {
    const { alertId } = req.params;
    const response = await fetch(`${FLASK_API_URL}/alerts/${alertId}/acknowledge`, {
      method: 'POST'
    });
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to acknowledge alert' });
  }
};

// Proxy route for KPIs
export const getKPIs: RequestHandler = async (req, res) => {
  try {
    const response = await fetch(`${FLASK_API_URL}/kpis`);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get KPIs' });
  }
};

// Proxy route for configuration
export const handleConfig: RequestHandler = async (req, res) => {
  try {
    const method = req.method;
    const options: any = { method };
    
    if (method === 'POST') {
      options.headers = { 'Content-Type': 'application/json' };
      options.body = JSON.stringify(req.body);
    }
    
    const response = await fetch(`${FLASK_API_URL}/config`, options);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to handle config' });
  }
};
'''

# 4. Updated server/index.ts with new routes
updated_server_index = '''
import "dotenv/config";
import express from "express";
import cors from "cors";
import { handleDemo, startProcessing, stopProcessing, getAlerts, acknowledgeAlert, getKPIs, handleConfig } from "./routes/api";
import multer from "multer";
import fetch from 'node-fetch';

// Configure multer for file uploads
const upload = multer({ dest: 'uploads/' });

export function createServer() {
  const app = express();
  
  // Middleware
  app.use(cors());
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  
  // Existing routes
  app.get("/api/ping", (_req, res) => {
    const ping = process.env.PING_MESSAGE ?? "ping";
    res.json({ message: ping });
  });
  
  app.get("/api/demo", handleDemo);
  
  // New Flask integration routes
  app.post("/api/start_processing", startProcessing);
  app.post("/api/stop_processing", stopProcessing);
  app.get("/api/alerts", getAlerts);
  app.post("/api/alerts/:alertId/acknowledge", acknowledgeAlert);
  app.get("/api/kpis", getKPIs);
  app.get("/api/config", handleConfig);
  app.post("/api/config", handleConfig);
  
  // File upload route
  app.post("/api/upload_video", upload.single('video'), async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No video file provided" });
      }
      
      // Forward to Flask backend
      const formData = new FormData();
      formData.append('video', req.file.buffer, req.file.originalname);
      
      const response = await fetch('http://localhost:5000/api/upload_video', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      res.status(500).json({ error: 'Failed to upload video' });
    }
  });
  
  // Camera setup route
  app.post("/api/set_camera", async (req, res) => {
    try {
      const response = await fetch('http://localhost:5000/api/set_camera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(req.body)
      });
      
      const data = await response.json();
      res.json(data);
    } catch (error) {
      res.status(500).json({ error: 'Failed to set camera' });
    }
  });
  
  return app;
}
'''

print("API integration files created!")
print("Files: server/routes/api.ts, server/index.ts updated")