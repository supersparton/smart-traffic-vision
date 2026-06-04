const canvas = document.getElementById('simCanvas');
const ctx = canvas.getContext('2d');
const statsContainer = document.getElementById('stats-container');
const globalTimer = document.getElementById('global-timer');
const laneFrames = {
    "North": document.getElementById('frame-North'),
    "East": document.getElementById('frame-East'),
    "South": document.getElementById('frame-South'),
    "West": document.getElementById('frame-West')
};

// Intersection Layout Constants
const WIDTH = canvas.width = 800;
const HEIGHT = canvas.height = 500;
const ROAD_WIDTH = 120;
const CTR_X = WIDTH / 2;
const CTR_Y = HEIGHT / 2;

const lanePositions = {
    "North": { x: CTR_X, y: CTR_Y - 100, rot: 0 },
    "South": { x: CTR_X, y: CTR_Y + 100, rot: Math.PI },
    "East": { x: CTR_X + 100, y: CTR_Y, rot: Math.PI/2 },
    "West": { x: CTR_X - 100, y: CTR_Y, rot: -Math.PI/2 }
};

function drawIntersection() {
    // Background
    ctx.fillStyle = '#f1f5f9';
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Roads (Horizontal & Vertical)
    ctx.fillStyle = '#e2e8f0';
    // Vertical road
    ctx.fillRect(CTR_X - ROAD_WIDTH/2, 0, ROAD_WIDTH, HEIGHT);
    // Horizontal road
    ctx.fillRect(0, CTR_Y - ROAD_WIDTH/2, WIDTH, ROAD_WIDTH);

    // Center Square
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(CTR_X-ROAD_WIDTH/2, CTR_Y-ROAD_WIDTH/2, ROAD_WIDTH, ROAD_WIDTH);
    
    // Lane Markings (Simplified)
    ctx.strokeStyle = '#fff';
    ctx.setLineDash([10, 10]);
    ctx.beginPath();
    ctx.moveTo(CTR_X, 0); ctx.lineTo(CTR_X, HEIGHT);
    ctx.moveTo(0, CTR_Y); ctx.lineTo(WIDTH, CTR_Y);
    ctx.stroke();
    ctx.setLineDash([]);
}

function drawLight(lane, state) {
    const pos = lanePositions[lane];
    const lightX = pos.x;
    const lightY = pos.y;
    
    // Light Box
    ctx.save();
    ctx.translate(lightX, lightY);
    ctx.rotate(pos.rot);
    
    ctx.fillStyle = '#000';
    ctx.fillRect(-15, -40, 30, 80);
    
    const colors = {
        red: state === 'RED' ? '#ef4444' : '#450a0a',
        yellow: state === 'YELLOW' ? '#f59e0b' : '#451a03',
        green: state === 'GREEN' ? '#10b981' : '#064e3b'
    };
    
    // Red
    drawCircle(0, -25, 10, colors.red, state === 'RED');
    // Yellow
    drawCircle(0, 0, 10, colors.yellow, state === 'YELLOW');
    // Green
    drawCircle(0, 25, 10, colors.green, state === 'GREEN');
    
    ctx.restore();
}

function drawCircle(x, y, r, color, glow) {
    if (glow) {
        ctx.shadowBlur = 15;
        ctx.shadowColor = color;
    }
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI*2);
    ctx.fill();
    ctx.shadowBlur = 0;
}

// Upload / Live Tabs
const tabUpload = document.getElementById('tab-upload');
const tabLive = document.getElementById('tab-live');
const uploadContent = document.getElementById('upload-mode-content');
const liveContent = document.getElementById('live-mode-content');
const startLiveBtn = document.getElementById('start-live-btn');
const startAnalysisBtn = document.getElementById('start-analysis-btn');

const lanes = ["North", "East", "South", "West"];
let laneLinks = {};

function updateFileName(lane) {
    const input = document.getElementById(`video-${lane}`);
    const small = document.getElementById(`name-${lane}`);
    if (input.files.length > 0) {
        small.innerText = input.files[0].name;
        small.style.color = "#10b981";
    }
}

tabUpload.onclick = () => {
    tabUpload.classList.add('active');
    tabLive.classList.remove('active');
    uploadContent.classList.remove('hidden');
    liveContent.classList.add('hidden');
};

tabLive.onclick = async () => {
    tabLive.classList.add('active');
    tabUpload.classList.remove('active');
    liveContent.classList.remove('hidden');
    uploadContent.classList.add('hidden');
    
    // Generate 4 codes
    const res = await fetch('/generate_codes');
    const codes = await res.json();
    
    lanes.forEach(lane => {
        const h2 = document.getElementById(`code-${lane}`);
        if (h2) h2.innerText = codes[lane];
        laneLinks[lane] = `${window.location.protocol}//${window.location.host}/mobile/${codes[lane]}`;
    });
};

function copyLink(lane) {
    const url = laneLinks[lane];
    if (!url) return;
    
    navigator.clipboard.writeText(url).then(() => {
        const btn = document.querySelector(`.code-item:has(#code-${lane}) .copy-btn`);
        const oldText = btn.innerText;
        btn.innerText = "✅ Copied!";
        btn.style.borderColor = "#10b981";
        btn.style.color = "#10b981";
        
        setTimeout(() => {
            btn.innerText = oldText;
            btn.style.borderColor = "";
            btn.style.color = "";
        }, 2000);
    });
}

startLiveBtn.onclick = () => {
    const formData = new FormData();
    formData.append('is_live', 'true');
    
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('upload-status').classList.remove('hidden');
    document.getElementById('dashboard-section').classList.remove('hidden');
    document.getElementById('upload-status').classList.add('hidden');
    
    // Clear all old frames and reset containers for live mode
    lanes.forEach(lane => {
        const img = laneFrames[lane];
        if (img) { img.src = ''; }
        const container = document.getElementById(`container-${lane}`);
        const stats = document.getElementById(`stats-${lane}`);
        if (container) container.style.display = '';
        if (stats) { stats.style.display = ''; stats.innerHTML = 'Waiting for stream...'; }
    });
    
    fetch('/upload', { method: 'POST', body: formData })
        .then(() => startSocket());
};

startAnalysisBtn.onclick = () => {
    const formData = new FormData();
    let filesAdded = 0;
    
    lanes.forEach(lane => {
        const input = document.getElementById(`video-${lane}`);
        if (input.files.length > 0) {
            formData.append('videos', input.files[0]);
            formData.append('lanes', lane); // Tag each file with its lane!
            filesAdded++;
        }
    });

    if (filesAdded === 0) {
        alert("Please select at least 1 video.");
        return;
    }

    formData.append('is_live', 'false');
    
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('upload-status').classList.remove('hidden');
    
    fetch('/upload', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            // Hide containers for lanes without videos
            const activeLanes = data.active_lanes || [];
            lanes.forEach(lane => {
                const container = document.getElementById(`container-${lane}`);
                const stats = document.getElementById(`stats-${lane}`);
                if (!activeLanes.includes(lane)) {
                    if (container) container.style.display = 'none';
                    if (stats) stats.style.display = 'none';
                }
            });
            startSocket();
        });
};

// WebSocket Real-time Update
let socket = null;

function startSocket() {
    if (socket) return;
    socket = io();

    socket.on('lane_update', (data) => {
        const { lane, frame, counts, breakdown, controller } = data;
        
        // 1. Update Monitor Wall (If frame exists)
        if (frame) {
            // Hide loading state on first frame
            document.getElementById('upload-status').classList.add('hidden');
            document.getElementById('dashboard-section').classList.remove('hidden');

            const bytes = new Uint8Array(frame.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            const blob = new Blob([bytes], {type: 'image/jpeg'});
            const img = laneFrames[lane];
            if (img) {
                if (img.src) URL.revokeObjectURL(img.src); // Memory safety
                img.src = URL.createObjectURL(blob);
            }

            // Update mini breakdown stats
            const statsBox = document.getElementById(`stats-${lane}`);
            if (statsBox && breakdown) {
                const summary = {};
                breakdown.forEach(d => {
                    summary[d.class] = (summary[d.class] || 0) + 1;
                });
                statsBox.innerHTML = Object.entries(summary)
                    .map(([cls, count]) => `<span>${cls}: ${count}</span>`)
                    .join(' | ') || "No vehicles detected";
            }
        }

        // 2. Update Stats & Highlight
        const status = controller;
        if (!status || !status.lanes || !status.lanes[lane]) return;
        
        const laneState = status.lanes[lane].state;
        
        // Stats
        const statItem = document.getElementById(`stat-${lane}`);
        if (statItem) {
            statItem.querySelector('.count').innerText = `${counts} veh / ${status.lanes[lane].pcu} PCU`;
            statItem.querySelector('.timer').innerText = `Allocated Green: ${status.lanes[lane].green_time}s`;
            statItem.querySelector('.progress-fill').style.width = `${(status.lanes[lane].green_time / 60) * 100}%`;
        }

        // Highlight
        const container = document.getElementById(`container-${lane}`);
        if (container) {
            if (laneState === 'GREEN') {
                container.style.borderColor = '#10b981';
                container.style.boxShadow = '0 0 15px rgba(16, 185, 129, 0.3)';
            } else if (laneState === 'YELLOW') {
                container.style.borderColor = '#f59e0b';
                container.style.boxShadow = '0 0 15px rgba(245, 158, 11, 0.3)';
            } else {
                container.style.borderColor = '';
                container.style.boxShadow = '';
            }
        }

        // 3. Update Canvas Simulation & Global Timer Status (Backend Sync)
        if (lane === "North") { 
            currentControllerState = status;
            lastSyncTime = Date.now();
            syncTimerValue = status.timer;
        }
    });
}

let currentControllerState = null;
let lastSyncTime = Date.now();
let syncTimerValue = 0;

function animate() {
    drawIntersection();
    
    // Smooth Timer Interpolation (Frontend side)
    if (currentControllerState) {
        const elapsedSinceSync = (Date.now() - lastSyncTime) / 1000;
        const smoothTimer = Math.max(0, syncTimerValue - elapsedSinceSync);
        
        globalTimer.innerText = `${currentControllerState.active_lane} is ${currentControllerState.current_state} - ${smoothTimer.toFixed(1)}s`;
        globalTimer.style.background = currentControllerState.current_state === 'GREEN' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
        globalTimer.style.color = currentControllerState.current_state === 'GREEN' ? '#10b981' : '#ef4444';

        if (currentControllerState.lanes) {
            lanes.forEach(lane => {
                const laneState = currentControllerState.lanes[lane].state;
                drawLight(lane, laneState);
            });
        }
    }
    
    requestAnimationFrame(animate);
}

// Initial draw and start animation
animate();
