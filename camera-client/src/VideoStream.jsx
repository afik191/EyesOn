import React, { useState, useEffect, useRef } from "react";

const VideoStream = () => {
  const [imageSrc, setImageSrc] = useState(null);
  const [status, setStatus] = useState("Disconnected");
  const [logs, setLogs] = useState([]);
  const [isTalking, setIsTalking] = useState(false); // מצב דיבור
  
  const ws = useRef(null);
  const logsEndRef = useRef(null);
  const mediaRecorderRef = useRef(null); // שמירת המקליט

  useEffect(() => {
    const connect = () => {
      // עדכן את ה-URL לכתובת הקבועה שלך במידה והשתנתה
      const socketUrl = "wss://solenoidally-nonbearded-rocco.ngrok-free.dev";

      setStatus("Connecting...");
      ws.current = new WebSocket(socketUrl);

      ws.current.onopen = () => {
        console.log("Connected");
        setStatus("Connected");
        addLog("System Connected to Interface");
      };

      ws.current.onmessage = (event) => {
        const data = event.data;
        if (typeof data === 'string' && data.startsWith("LOG:")) {
          addLog(data.substring(4));
        } else {
          setImageSrc(`data:image/jpeg;base64,${data}`);
        }
      };

      ws.current.onclose = () => {
        setStatus("Disconnected");
        setTimeout(connect, 2000);
      };

      ws.current.onerror = (err) => {
        console.error("Error:", err);
        ws.current.close();
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prevLogs => [`[${timestamp}] ${message}`, ...prevLogs].slice(0, 50));
  };

  // --- פונקציות דיבור (Walkie Talkie) ---
  const startTalking = async () => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) return;

    try {
      // בקשת גישה למיקרופון
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // יצירת מקליט בפורמט webm (ש-ffmpeg יודע לקרוא)
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws.current.readyState === WebSocket.OPEN) {
          // שליחת המידע הבינארי לסוקט
          ws.current.send(event.data);
        }
      };

      // שליחת חתיכות מידע כל 100ms כדי שהדיבור יהיה רציף
      mediaRecorder.start(100);
      setIsTalking(true);
      addLog("🎤 Sending Audio...");
    } catch (err) {
      console.error("Mic Error:", err);
      addLog("Error: Check Microphone Permissions");
    }
  };

  const stopTalking = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      // כיבוי המיקרופון כדי לשחרר משאבים
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    setIsTalking(false);
    addLog("🎤 Microphone Muted");
  };

  return (
    <div className="page-container">
      <div className="glass-card">
        
        {/* Header */}
        <div className="card-header">
          <div className="header-text">
            <h1 className="app-title">EyesOn</h1>
            <p className="subtitle">RPi 5 Neural Surveillance</p>
          </div>
          <div className={`status-pill ${status.toLowerCase()}`}>
            <span className="status-dot"></span>
            {status}
          </div>
        </div>

        {/* Video Frame */}
        <div className="video-frame">
          {imageSrc ? (
            <>
              <div className="camera-overlay">
                <div className="rec-badge"><span className="rec-dot"></span> REC</div>
                <div className="live-badge">LIVE</div>
              </div>
              <img className="stream-image" src={imageSrc} alt="Live Stream" />
            </>
          ) : (
            <div className="placeholder">
              <div className="scanner"></div>
              <p>Establishing Secure Link...</p>
            </div>
          )}
        </div>

        {/* --- TALK BUTTON --- */}
        <div className="controls-area">
            <button 
                className={`talk-btn ${isTalking ? 'active' : ''}`}
                onMouseDown={startTalking}
                onMouseUp={stopTalking}
                onTouchStart={startTalking} // לנייד
                onTouchEnd={stopTalking}    // לנייד
            >
                <div className="mic-icon">🎙️</div>
                {isTalking ? "RELEASE TO MUTE" : "HOLD TO TALK"}
            </button>
        </div>

        {/* Logs Terminal */}
        <div className="logs-container">
          <div className="logs-header">SYSTEM LOGS</div>
          <div className="logs-content">
            {logs.length === 0 ? <div className="log-item waiting">Waiting for logs...</div> : 
             logs.map((log, index) => (
                <div key={index} className="log-item"><span className="log-arrow">{">"}</span> {log}</div>
             ))}
            <div ref={logsEndRef} />
          </div>
        </div>
        
        {/* Footer */}
        <div className="card-footer">
          <span>System: <strong>Active</strong></span>
          <span>Latency: <strong>Low</strong></span>
          <span>Model: <strong>YOLOv11</strong></span>
        </div>
      </div>

      <style jsx>{`
        /* ... כל הסטיילים הקודמים נשארים זהים, הוספתי רק את הכפתור ... */
        
        /* (כל הקוד הקיים של page-container, glass-card וכו' נשאר...) */
        .page-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; background: radial-gradient(circle at center, #1a1a1a 0%, #000000 100%); font-family: 'Inter', sans-serif; color: white; overflow: hidden; z-index: 9999; }
        .glass-card { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; padding: 24px; width: 90%; max-width: 800px; height: 90vh; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); display: flex; flex-direction: column; gap: 16px; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        .app-title { margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -1px; background: linear-gradient(to right, #ffffff, #a5a5a5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { margin: 2px 0 0 0; font-size: 0.7rem; color: rgba(255, 255, 255, 0.4); text-transform: uppercase; letter-spacing: 2px; }
        
        .status-pill { display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 99px; font-size: 0.7rem; font-weight: 600; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; }
        .connected { color: #4ade80; border-color: rgba(74, 222, 128, 0.2); }
        .connected .status-dot { background: #4ade80; box-shadow: 0 0 10px #4ade80; }
        .connecting { color: #fbbf24; }
        .connecting .status-dot { background: #fbbf24; animation: blink 1s infinite; }
        .disconnected { color: #f87171; }
        .disconnected .status-dot { background: #f87171; }
        
        .video-frame { position: relative; width: 100%; aspect-ratio: 16/9; background: #000; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0 0 40px rgba(0,0,0,0.5); flex-shrink: 0; }
        .stream-image { width: 100%; height: 100%; object-fit: cover; }
        .camera-overlay { position: absolute; top: 16px; left: 16px; right: 16px; display: flex; justify-content: space-between; z-index: 10; }
        .rec-badge { background: rgba(220, 38, 38, 0.2); color: #ef4444; padding: 4px 10px; border-radius: 6px; font-size: 0.65rem; font-weight: 800; display: flex; align-items: center; gap: 6px; border: 1px solid rgba(239, 68, 68, 0.3); backdrop-filter: blur(4px); }
        .rec-dot { width: 6px; height: 6px; background: #ef4444; border-radius: 50%; animation: blink 1s infinite; }
        .live-badge { background: rgba(0, 0, 0, 0.5); color: #fff; padding: 4px 8px; border-radius: 6px; font-size: 0.65rem; font-weight: 700; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(4px); }

        /* --- STYLES FOR TALK BUTTON --- */
        .controls-area { display: flex; justify-content: center; padding: 5px; }
        .talk-btn { background: linear-gradient(145deg, #1e1e1e, #2a2a2a); border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); padding: 15px 30px; border-radius: 50px; font-weight: 700; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 10px; transition: all 0.2s ease; width: 100%; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); user-select: none; -webkit-user-select: none; }
        .talk-btn:active, .talk-btn.active { background: #ef4444; color: white; transform: scale(0.98); box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); border-color: #ef4444; }
        .mic-icon { font-size: 1.2rem; }

        .logs-container { flex-grow: 1; background: rgba(0, 0, 0, 0.6); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px; display: flex; flex-direction: column; overflow: hidden; font-family: 'Courier New', monospace; }
        .logs-header { font-size: 0.7rem; color: rgba(255, 255, 255, 0.3); margin-bottom: 8px; letter-spacing: 1px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 4px; }
        .logs-content { flex-grow: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
        .logs-content::-webkit-scrollbar { width: 6px; }
        .logs-content::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 3px; }
        .log-item { font-size: 0.8rem; color: #10b981; line-height: 1.4; }
        .log-arrow { color: #059669; margin-right: 4px; }
        .log-item.waiting { color: rgba(255, 255, 255, 0.2); font-style: italic; }
        .placeholder { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: rgba(255, 255, 255, 0.3); }
        .scanner { width: 100%; height: 1px; background: linear-gradient(90deg, transparent, #4ade80, transparent); position: absolute; top: 50%; animation: scan 2s ease-in-out infinite; opacity: 0.5; }
        .card-footer { display: flex; justify-content: space-between; padding: 0 5px; font-size: 0.7rem; color: rgba(255, 255, 255, 0.3); }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes scan { 0% { top: 0%; } 100% { top: 100%; } }
      `}</style>
    </div>
  );
};

export default VideoStream;