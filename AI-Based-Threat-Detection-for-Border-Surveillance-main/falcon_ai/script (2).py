# 5. Updated LiveMonitor.tsx with real WebSocket integration
updated_live_monitor = '''
import KPITile from "@/components/falcon/KPITile";
import LiveChip from "@/components/falcon/LiveChip";
import DirectionPill from "@/components/falcon/DirectionPill";
import AlertCard from "@/components/falcon/AlertCard";
import { AlertItem } from "@shared/api";
import { ChevronDown, Clock3, Gauge, Inbox, Radio, Users, Play, Square, Upload, Camera } from "lucide-react";
import { useEffect, useMemo, useState, useRef } from "react";
import { toast } from "sonner";
import io from 'socket.io-client';

export default function LiveMonitor() {
  const [env, setEnv] = useState("Live Processing");
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [showLegend, setShowLegend] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [kpis, setKpis] = useState({
    currentFPS: "30",
    avgLatency: "1.2s", 
    activeTracks: "0",
    alertsLast24h: "0"
  });
  const [videoFrame, setVideoFrame] = useState<string | null>(null);
  
  const socketRef = useRef<any>(null);
  const videoCanvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Connect to Flask SocketIO server
    socketRef.current = io('http://localhost:5000');
    
    socketRef.current.on('connect', () => {
      console.log('Connected to Falcon AI backend');
    });
    
    socketRef.current.on('video_frame', (data: any) => {
      setVideoFrame(data.frame);
      if (data.kpis) {
        setKpis({
          currentFPS: data.kpis.currentFPS.toString(),
          avgLatency: data.kpis.avgLatency,
          activeTracks: data.kpis.activeTracks.toString(),
          alertsLast24h: data.kpis.alertsLast24h.toString()
        });
      }
      
      // Draw detections on canvas
      if (videoCanvasRef.current && data.detections) {
        drawDetections(data.detections, data.fence_line_y);
      }
    });
    
    socketRef.current.on('alert_detected', (alert: AlertItem) => {
      setAlerts(prev => [alert, ...prev]);
      toast.error("New Threat Alert!", {
        description: `Person #${alert.trackId} - ${alert.type} detected at ${alert.site}`,
      });
    });
    
    socketRef.current.on('new_alert', (data: any) => {
      toast.info("Alert Sent", {
        description: data.message
      });
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Draw video frame and detections on canvas
  useEffect(() => {
    if (videoFrame && videoCanvasRef.current) {
      const canvas = videoCanvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const img = new Image();
        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
        };
        img.src = `data:image/jpeg;base64,${videoFrame}`;
      }
    }
  }, [videoFrame]);

  const drawDetections = (detections: any[], fenceLineY: number) => {
    const canvas = videoCanvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Draw fence line
    ctx.strokeStyle = '#3B82F6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, fenceLineY);
    ctx.lineTo(canvas.width, fenceLineY);
    ctx.stroke();
    
    // Draw detections
    detections.forEach(detection => {
      const [x1, y1, x2, y2] = detection.bbox;
      
      // Draw bounding box
      ctx.strokeStyle = '#10B981';
      ctx.lineWidth = 2;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
      
      // Draw track ID
      ctx.fillStyle = '#10B981';
      ctx.font = '14px Arial';
      ctx.fillText(`#${detection.trackId}`, x1, y1 - 5);
      
      // Draw direction if available
      if (detection.direction) {
        ctx.fillStyle = detection.direction.includes('push-in') ? '#EF4444' : '#10B981';
        ctx.fillText(detection.direction, x1, y2 + 15);
      }
    });
  };

  const startProcessing = async () => {
    try {
      const response = await fetch('/api/start_processing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (response.ok) {
        setIsProcessing(true);
        toast.success("Processing Started", {
          description: "Video analysis is now active"
        });
      }
    } catch (error) {
      toast.error("Failed to start processing");
    }
  };

  const stopProcessing = async () => {
    try {
      const response = await fetch('/api/stop_processing', {
        method: 'POST'
      });
      
      if (response.ok) {
        setIsProcessing(false);
        toast.info("Processing Stopped");
      }
    } catch (error) {
      toast.error("Failed to stop processing");
    }
  };

  const handleVideoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await fetch('/api/upload_video', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        toast.success("Video uploaded successfully");
        // Automatically start processing the uploaded video
        await startProcessing();
      }
    } catch (error) {
      toast.error("Failed to upload video");
    }
  };

  const handleCameraSetup = async () => {
    try {
      const response = await fetch('/api/set_camera', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ camera_id: 0 })
      });

      if (response.ok) {
        toast.success("Camera connected");
        await startProcessing();
      }
    } catch (error) {
      toast.error("Failed to connect camera");
    }
  };

  const kpiTiles = useMemo(
    () => [
      { label: "Current FPS", value: kpis.currentFPS, icon: <Gauge className="h-4 w-4" /> },
      { label: "Avg Latency", value: kpis.avgLatency, icon: <Clock3 className="h-4 w-4" /> },
      { label: "Active Tracks", value: kpis.activeTracks, icon: <Users className="h-4 w-4" /> },
      { label: "Alerts last 24h", value: kpis.alertsLast24h, icon: <Inbox className="h-4 w-4" /> },
    ],
    [kpis],
  );

  const acknowledge = async (id: string) => {
    try {
      const response = await fetch(`/api/alerts/${id}/acknowledge`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: "acknowledged" } : a));
        toast.success("Alert acknowledged");
      }
    } catch (error) {
      toast.error("Failed to acknowledge alert");
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Falcon AI — Live Monitor</h1>
        <div className="flex items-center gap-4">
          {/* Video Source Controls */}
          <div className="flex gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Upload className="h-4 w-4" />
              Upload Video
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleVideoUpload}
              className="hidden"
            />
            
            <button
              onClick={handleCameraSetup}
              className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <Camera className="h-4 w-4" />
              Use Camera
            </button>
          </div>
          
          {/* Processing Controls */}
          <div className="flex gap-2">
            <button
              onClick={isProcessing ? stopProcessing : startProcessing}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                isProcessing 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isProcessing ? (
                <>
                  <Square className="h-4 w-4" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start
                </>
              )}
            </button>
          </div>
          
          <LiveChip />
        </div>
      </div>

      {/* KPI Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiTiles.map((k) => (
          <KPITile key={k.label} {...k} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Video Viewport */}
        <div className="lg:col-span-2">
          <div className="bg-card rounded-xl border shadow-card p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Live Video Feed</h2>
              <button
                onClick={() => setShowLegend(!showLegend)}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                {showLegend ? "Hide" : "Show"} Legend
              </button>
            </div>
            
            <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '16/9' }}>
              <canvas
                ref={videoCanvasRef}
                className="w-full h-full object-contain"
                style={{ maxHeight: '400px' }}
              />
              
              {!videoFrame && (
                <div className="absolute inset-0 flex items-center justify-center text-white">
                  <div className="text-center">
                    <Camera className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No video feed</p>
                    <p className="text-sm opacity-75">Upload a video or connect camera to start</p>
                  </div>
                </div>
              )}
              
              {/* Processing Status Overlay */}
              {isProcessing && (
                <div className="absolute top-4 left-4">
                  <div className="flex items-center gap-2 bg-red-600 text-white px-3 py-1 rounded-full text-sm">
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                    LIVE
                  </div>
                </div>
              )}
            </div>

            {showLegend && (
              <div className="mt-4 flex flex-wrap gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-blue-500"></div>
                  <span>Fence Line</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-green-500"></div>
                  <span>Person Detection</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span>Push-In Alert</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span>Push-Out Alert</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Alert Feed */}
        <div>
          <div className="bg-card rounded-xl border shadow-card p-4">
            <h2 className="text-lg font-semibold mb-4">Recent Alerts</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No alerts yet</p>
              ) : (
                alerts.map((alert) => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                    onAck={acknowledge}
                    onOpen={() => {}}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
'''

print("Updated LiveMonitor.tsx with real WebSocket integration!")
print("This connects to your Flask backend for real-time video processing")