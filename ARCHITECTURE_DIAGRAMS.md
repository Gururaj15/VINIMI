# VINIMI Architecture - Updated Mermaid Diagrams (v2.0+)

## System Architecture Diagram (Updated)

```mermaid
graph TB
    User["👤 User<br/>Browser"]
    
    subgraph Frontend["🎨 Frontend Layer (React + Vite)"]
        Home["🏠 Home"]
        Auth["🔐 Auth<br/>Login/Signup"]
        Dashboard["📊 Dashboard"]
        Workers["👥 Workers<br/>List & Details"]
        Live["📹 Live<br/>Monitoring"]
        AskVLM["🤖 Ask VLM<br/>Image/Video Analysis"]
        Violations["⚠️ Violations<br/>History"]
        Alerts["🔔 Recent<br/>Alerts"]
        Account["⚙️ Account<br/>Settings"]
    end
    
    subgraph Backend["⚙️ Backend Layer (FastAPI)"]
        Routes["🌐 API Routes<br/>25+ endpoints"]
        Auth_BE["🔐 Auth<br/>Manager Login"]
        Workers_BE["👥 Worker<br/>Management"]
        RegSession["📝 Registration<br/>Sessions (NEW)"]
        Detection["🎯 Detection<br/>Orchestration"]
        VLM["🤖 VLM Integration<br/>(NEW)"]
        Tasks["📋 Background<br/>Tasks"]
    end
    
    subgraph AI["🧠 AI/ML Services"]
        YOLO["🔍 YOLO v8<br/>Helmet Detection"]
        DeepFace["👤 DeepFace<br/>Face Recognition"]
        Gallery["📚 Face Gallery<br/>Vector Search"]
        Qwen["🤖 Qwen VLM<br/>Vision Language (NEW)"]
        VideoProc["🎬 Video Processing<br/>(NEW)"]
    end
    
    subgraph Storage["💾 Storage Layer"]
        MySQL["🗄️ MySQL<br/>vinimi_local"]
        FileSystem["📁 File System<br/>Images/Logs/Videos"]
        CSV["📊 Embeddings CSV<br/>(NEW)"]
    end
    
    External["🚀 External<br/>Twilio + HF API"]
    
    User -->|HTTP/REST| Frontend
    Frontend -->|API Calls| Backend
    Backend -->|Query| Routes
    Routes -->|Process| Auth_BE
    Routes -->|Manage| Workers_BE
    Routes -->|Manage| RegSession
    Routes -->|Analyze| Detection
    Routes -->|Query VLM| VLM
    Routes -->|Async| Tasks
    
    Detection -->|Detect| YOLO
    Detection -->|Extract| DeepFace
    Detection -->|Search| Gallery
    VLM -->|Query| Qwen
    VLM -->|Frame Sampling| VideoProc
    Gallery -->|Load| MySQL
    
    RegSession -->|Store| FileSystem
    RegSession -->|Store| MySQL
    
    Tasks -->|SMS| External
    Tasks -->|Store| FileSystem
    VLM -->|API| External
    
    Backend -->|Read/Write| MySQL
    Backend -->|Save| FileSystem
    Backend -->|Read/Write| CSV
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style AI fill:#f3e5f5
    style Storage fill:#e8f5e9
```

---

## Frontend Architecture - Updated Pages

```mermaid
graph TB
    App["App.tsx<br/>Router Setup"]
    
    Public["🌐 Public Pages"]
    Auth_Pages["🔐 Auth Pages"]
    Protected["🔒 Protected Pages"]
    
    subgraph Public_Routes["Public Access"]
        Home["/ → Home.tsx<br/>Marketing Landing"]
        NotFound["* → NotFound.tsx<br/>404 Page"]
    end
    
    subgraph Auth_Routes["Authentication"]
        Login["​/login → Login.tsx<br/>Manager Login"]
        Signup["​/signup → Signup.tsx<br/>New Account"]
    end
    
    subgraph Protected_Routes["Protected<br/>✓ Auth Required"]
        Dashboard["​/dashboard → Dashboard.tsx<br/>KPIs & Overview"]
        Workers_Page["​/workers → Workers.tsx<br/>Worker List"]
        Worker_Detail["​/workers/:id → WorkerDetail.tsx<br/>Worker Profile"]
        Live_Mon["​/live → LiveMonitoring.tsx<br/>Real-time Monitoring"]
        Ask_VLM["​/ask-vlm → AskVLM.tsx<br/>Image/Video VLM Analysis (NEW)"]
        Violations_Page["​/violations → Violations.tsx<br/>Violation History"]
        Recent["​/recent-alerts → RecentAlerts.tsx<br/>Recent SMS Alerts"]
        Account_Page["​/account → Account.tsx<br/>Profile Settings"]
    end
    
    App --> Public
    App --> Auth_Pages
    App --> Protected
    
    Public --> Public_Routes
    Auth_Pages --> Auth_Routes
    Protected --> Protected_Routes
    
    Auth_Routes -->|Login Success<br/>Token Stored| Protected_Routes
    Protected_Routes -->|Logout| Auth_Routes
    
    style App fill:#fff9c4
    style Public fill:#c8e6c9
    style Auth_Pages fill:#ffccbc
    style Protected fill:#bbdefb
    style Auth_Routes fill:#ffccbc
    style Protected_Routes fill:#bbdefb
    style Ask_VLM fill:#f3e5f5
```

---

## API Endpoint Map - Updated (25+ routes)

```mermaid
graph TB
    API["FastAPI<br/>http://localhost:8001"]
    
    subgraph Auth["🔐 Authentication (4)"]
        SIGNUP["POST /auth/signup"]
        LOGIN["POST /auth/login"]
        MSIGNUP["POST /api/manager/signup"]
        MLOGIN["POST /api/manager/login"]
    end
    
    subgraph Workers["👥 Workers (5)"]
        LIST_W["GET /api/workers"]
        GET_W["GET /api/workers/{id}"]
        MEDIA_W["GET /api/workers/{id}/media"]
        VIOLATIONS_W["GET /api/workers/{id}/violations"]
        MANAGER_W["GET/PUT /api/manager/{id}"]
    end
    
    subgraph RegSession["📝 Registration (3) - NEW"]
        START["POST /api/workers/register/start"]
        CAPTURE["POST /api/workers/register/capture"]
        COMPLETE["POST /api/workers/register/complete"]
    end
    
    subgraph Detection["🎯 Detection (2)"]
        DETECT["POST /api/detect/frame"]
        LIVE["POST /api/live/frame"]
    end
    
    subgraph VLM["🤖 VLM Analysis (1) - NEW"]
        ASKVLM["POST /api/ask-vlm"]
    end
    
    subgraph Alerts["🔔 Alerts (2)"]
        RECALERTS["GET /api/live/recent-alerts"]
        TEST_ALERT["POST /api/alerts/test"]
    end
    
    subgraph Violations["⚠️ Violations (1)"]
        LIST_V["GET /api/violations"]
    end
    
    subgraph Logs["📋 Logs (5)"]
        LIST_L["GET /api/logs/list"]
        TAIL_L["GET /api/logs/tail"]
        TODAY_L["GET /api/logs/today"]
        PDF_L["GET /api/logs/today.pdf"]
        DL_L["GET /api/logs/download"]
    end
    
    Health["GET /health"]
    
    API --> Auth
    API --> Workers
    API --> RegSession
    API --> Detection
    API --> VLM
    API --> Alerts
    API --> Violations
    API --> Logs
    API --> Health
    
    style API fill:#ffe0b2
    style Auth fill:#c8e6c9
    style Workers fill:#bbdefb
    style RegSession fill:#f3e5f5
    style Detection fill:#f8bbd0
    style VLM fill:#f3e5f5
    style Alerts fill:#ffe0b2
    style Violations fill:#ffe0b2
    style Logs fill:#e1bee7
```

---

## Multi-Sample Registration Flow (NEW)

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>React
    participant Backend as Backend<br/>FastAPI
    participant DeepFace as DeepFace
    participant FileSystem as File System
    participant MySQL as MySQL
    participant Gallery as Face Gallery
    
    User->>Frontend: Click "Register Worker"
    Frontend->>Backend: POST /api/workers/register/start
    Backend->>Backend: Create session (UUID, 120s timeout)
    Backend-->>Frontend: {session_id, target_samples: 7}
    
    Frontend->>User: Show capture UI<br/>Instruction: "Face the camera"
    
    loop Capture 7 samples
        User->>Frontend: Take pose sample
        Frontend->>Backend: POST /api/workers/register/capture<br/>{session_id, pose_hint, frame}
        
        Backend->>DeepFace: Extract face + embedding
        DeepFace-->>Backend: {crop, embedding[128]}
        
        Backend->>Backend: Add to session.collected[]
        Backend-->>Frontend: {status, collected: N/7}
        Frontend->>User: Update progress bar
    end
    
    Frontend->>Frontend: All samples collected
    Frontend->>User: Show confirmation form
    User->>Frontend: Enter name, phone, company, location
    
    Frontend->>Backend: POST /api/workers/register/complete<br/>{session_id, name, phone, ...}
    
    Backend->>Backend: Aggregate embeddings<br/>agg = mean(7_embeddings)
    
    Backend->>FileSystem: Save representative frame
    Backend->>FileSystem: Append to embeddings CSV
    
    Backend->>MySQL: INSERT worker
    Backend->>MySQL: INSERT embedding (agg)
    Backend->>MySQL: INSERT worker_image
    
    Backend->>Gallery: reload_gallery()
    Gallery->>MySQL: Fetch all embeddings
    MySQL-->>Gallery: Updated vectors
    
    Backend-->>Frontend: {status: "ok", worker_id: 123}
    Frontend->>User: Success! "Worker registered"
```

---

## VLM Analysis Workflow (NEW)

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>React
    participant Backend as Backend<br/>FastAPI
    participant YOLO as YOLO v8
    participant DeepFace as DeepFace
    participant VideoProc as Video Module
    participant VLM as Qwen VLM<br/>HuggingFace
    participant MySQL as MySQL
    
    User->>Frontend: Upload image/video + question
    Frontend->>Backend: POST /api/ask-vlm
    
    alt Image Upload
        Backend->>YOLO: Detect helmets
        Backend->>DeepFace: Extract faces
        DeepFace-->>Backend: Face embeddings
        Backend->>MySQL: Search gallery
        Backend->>Backend: Compile detector facts
    else Video Upload
        Backend->>VideoProc: analyze_video_face_recognition()
        VideoProc->>VideoProc: Sample 10 frames
        loop Each frame
            VideoProc->>YOLO: Helmet detection
            VideoProc->>DeepFace: Face extraction
            VideoProc->>MySQL: Gallery search
        end
        VideoProc->>VideoProc: Voting on worker
        VideoProc-->>Backend: segments[], majority_worker
        Backend->>Backend: Extract representative frame
    end
    
    Backend->>Backend: Resize image for VLM (512px)
    Backend->>Backend: Base64 encode
    Backend->>Backend: Create system prompt
    Backend->>Backend: Inject detector facts as JSON
    
    Backend->>VLM: POST /chat/completions<br/>{model, messages, max_tokens}
    VLM-->>Backend: Reasoning response
    
    Backend->>Backend: Compile response<br/>{person, ppe, faces, reasoning, ...}
    Backend-->>Frontend: Analysis result
    
    Frontend->>Frontend: Render results
    Frontend->>User: Show worker info + VLM reasoning
```

---

## Video Frame Analysis Detail (NEW)

```mermaid
graph TB
    VidInput["📹 Video Input"]
    
    subgraph Processing["Frame Sampling & Analysis"]
        Load["Load embeddings CSV"]
        Sample["Sample N frames<br/>(default: 10)"]
        Analyze["Analyze each frame"]
    end
    
    subgraph PerFrame["Per-Frame Analysis"]
        Cascade["Face detection<br/>(Cascade)"]
        Extract["Extract face crop"]
        Embed["DeepFace embedding<br/>(VGG-Face)"]
        Search["Cosine similarity<br/>search"]
        YOLO_VID["YOLO helmet<br/>detection"]
        Result["Create segment<br/>result"]
    end
    
    subgraph Voting["Majority Voting"]
        Counter["Count worker names"]
        Vote["Find most common"]
        Majority["Set majority worker"]
    end
    
    subgraph Output["Output Generation"]
        Segments["segments[] with<br/>per-frame results"]
        Representative["Select representative<br/>frame (first match)"]
        Summary["Summary with majority<br/>& confidence"]
        Video["Optional: annotated<br/>video with bboxes"]
    end
    
    VidInput --> Processing
    Processing --> Load
    Load --> Sample
    Sample --> Analyze
    Analyze --> PerFrame
    
    PerFrame --> Cascade
    Cascade --> Extract
    Extract --> Embed
    Embed --> Search
    Cascade --> YOLO_VID
    Search --> Result
    YOLO_VID --> Result
    
    Result --> Voting
    Voting --> Counter
    Counter --> Vote
    Vote --> Majority
    
    Majority --> Output
    Output --> Segments
    Output --> Representative
    Output --> Summary
    Output --> Video
    
    style VidInput fill:#ffcccc
    style Processing fill:#fff9c4
    style PerFrame fill:#bbdefb
    style Voting fill:#f8bbd0
    style Output fill:#c8e6c9
```

---

## Endpoint Dependencies & Data Flow

```mermaid
graph LR
    Start["User Action"]
    
    Auth["📝 Auth Endpoints<br/>signup/login"]
    RegStart["📝 /register/start<br/>Create session"]
    RegCapture["📸 /register/capture<br/>Collect samples"]
    RegComplete["✅ /register/complete<br/>Save worker"]
    Live["📹 /api/live/frame<br/>Stream detection"]
    Detect["🔍 /api/detect/frame<br/>Single detection"]
    AskVLM["🤖 /api/ask-vlm<br/>VLM analysis"]
    
    DB["💾 MySQL"]
    Gallery["📚 Face Gallery"]
    CSV["📊 Embeddings CSV"]
    
    Start -->|Login| Auth
    Auth -->|Authenticated| RegStart
    RegStart -->|Session created| RegCapture
    RegCapture -->|Samples collected| RegComplete
    RegComplete -->|Save| DB
    RegComplete -->|Update| Gallery
    RegComplete -->|Append| CSV
    
    Start -->|Live stream| Live
    Live -->|Search| Gallery
    Live -->|Save violation| DB
    
    Start -->|Single frame| Detect
    Detect -->|Analyze| Gallery
    
    Start -->|Ask question| AskVLM
    AskVLM -->|Get embeddings| CSV
    AskVLM -->|Search workers| DB
    AskVLM -->|Call VLM| Qwen["🤖 Qwen VLM"]
    
    style Start fill:#ffcccc
    style Auth fill:#c8e6c9
    style RegStart fill:#ffe0b2
    style RegCapture fill:#ffe0b2
    style RegComplete fill:#ffe0b2
    style Live fill:#f8bbd0
    style Detect fill:#f8bbd0
    style AskVLM fill:#f3e5f5
    style DB fill:#e1bee7
    style Gallery fill:#bbdefb
    style CSV fill:#bbdefb
    style Qwen fill:#f3e5f5
```

---

## Configuration & Environment Variables (NEW)

```mermaid
graph TB
    subgraph VLMConfig["VLM Configuration"]
        VLM_BASE["VLM_BASE<br/>default: HF router"]
        VLM_MODEL["VLM_MODEL<br/>default: Qwen2.5-VL-7B"]
        VLM_API_KEY["VLM_API_KEY<br/>HuggingFace token"]
        VLM_TIMEOUT["VLM_TIMEOUT<br/>default: 120s"]
        VLM_ENABLED["VLM_ENABLED<br/>default: true"]
    end
    
    subgraph RegConfig["Registration Configuration"]
        REG_TARGET["REG_TARGET_SAMPLES<br/>default: 7"]
        REG_TIMEOUT["REG_SESSION_TIMEOUT<br/>default: 120s"]
    end
    
    subgraph FileConfig["File Storage"]
        MEDIA_ROOT["MEDIA_ROOT<br/>images, videos, violations"]
        LOGS_DIR["LOGS_DIR<br/>Daily JSON logs"]
        EMBEDDINGS_CSV["EMBEDDINGS_CSV<br/>Face vectors"]
    end
    
    subgraph DBConfig["Database Configuration"]
        LOCAL_DB_HOST["LOCAL_DB_HOST<br/>localhost"]
        LOCAL_DB_PORT["LOCAL_DB_PORT<br/>3306"]
        LOCAL_DB_USER["LOCAL_DB_USER<br/>root"]
        LOCAL_DB_PASS["LOCAL_DB_PASSWORD"]
        LOCAL_DB_NAME["LOCAL_DB_NAME<br/>vinimi_local"]
    end
    
    subgraph DetectionConfig["Detection Configuration"]
        YOLO_PATH["YOLO_MODEL_PATH<br/>best.pt"]
        FACE_THRESHOLD["FACE_SIM_THRESHOLD<br/>default: 0.7"]
    end
    
    style VLMConfig fill:#f3e5f5
    style RegConfig fill:#ffe0b2
    style FileConfig fill:#e8f5e9
    style DBConfig fill:#bbdefb
    style DetectionConfig fill:#f8bbd0
```

---

## Registration Session Lifecycle (NEW)

```mermaid
stateDiagram-v2
    [*] --> Init: /register/start
    
    Init --> Collecting: Session created<br/>(session_id, 120s TTL)
    
    Collecting --> Collecting: /register/capture<br/>Face detected, sample added<br/>(collected < 7)
    
    Collecting --> ReadyComplete: Enough samples<br/>(collected >= 7)
    
    Collecting --> Timeout: 120s elapsed<br/>Session auto-deleted
    
    ReadyComplete --> Completed: /register/complete<br/>Form submitted
    
    Completed --> [*]: Worker saved<br/>Gallery updated
    
    Timeout --> [*]: Session expired
    
    note right of Collecting
        Max 7 samples
        One pose per capture
        Each sample: frame → face → embedding
    end
    
    note right of Completed
        1. Aggregate embeddings (mean)
        2. Save to CSV
        3. Save to MySQL (worker, embedding, image)
        4. Reload gallery
    end
```

---

## Technology Stack Update (v2.0+)

```mermaid
graph TB
    subgraph Frontend["FRONTEND<br/>React Stack"]
        React["⚛️ React 18"]
        Vite["⚡ Vite Bundler"]
        TS["📘 TypeScript"]
        Tailwind["🎨 Tailwind CSS"]
        ShadCN["🧩 shadcn/ui"]
        RQ["📊 React Query"]
        Framer["✨ Framer Motion"]
    end
    
    subgraph Backend["BACKEND<br/>Python Stack"]
        FastAPI["⚙️ FastAPI"]
        Uvicorn["🚀 Uvicorn"]
        Pydantic["✓ Pydantic"]
        YOLO["🔍 YOLO v8"]
        DeepFace["👤 DeepFace"]
        OpenCV["📷 OpenCV"]
        Twilio["📱 Twilio SDK"]
        Requests["🌐 Requests (VLM)"]
        Pandas["📊 Pandas (CSV)"]
    end
    
    subgraph AI["AI/ML MODELS"]
        YOLO_M["YOLO v8<br/>Object Detection"]
        VGG["VGG-Face<br/>Face Embeddings"]
        Cascade["Haar Cascade<br/>Face Detection"]
        Qwen["🤖 Qwen VLM<br/>Vision Language"]
    end
    
    subgraph Database["DATABASE<br/>Data Stack"]
        MySQL["🗄️ MySQL 8.x"]
        Redis["🔴 Redis (optional)"]
        CSV["📄 CSV Files<br/>(NEW)"]
    end
    
    subgraph DevOps["DEVOPS & EXTERNAL"]
        Docker["🐳 Docker"]
        HF["🤗 HuggingFace API<br/>(NEW)"]
        Twilio_API["Twilio API"]
    end
    
    Frontend --> React
    Frontend --> Vite
    Frontend --> TS
    Frontend --> Tailwind
    Frontend --> ShadCN
    Frontend --> RQ
    Frontend --> Framer
    
    Backend --> FastAPI
    Backend --> Uvicorn
    Backend --> Pydantic
    Backend --> YOLO
    Backend --> DeepFace
    Backend --> OpenCV
    Backend --> Twilio
    Backend --> Requests
    Backend --> Pandas
    
    AI --> YOLO_M
    AI --> VGG
    AI --> Cascade
    AI --> Qwen
    
    Database --> MySQL
    Database --> Redis
    Database --> CSV
    
    DevOps --> Docker
    DevOps --> HF
    DevOps --> Twilio_API
    
    style Frontend fill:#bbdefb
    style Backend fill:#fff9c4
    style AI fill:#f3e5f5
    style Database fill:#e1bee7
    style DevOps fill:#c8e6c9
```

---

## Performance & Scalability Roadmap

```mermaid
graph TB
    subgraph Phase1["Phase 1: Current (v2.0)"]
        Single["Single server deployment"]
        LocalMySQL["Local MySQL"]
        InMemGallery["In-memory face gallery"]
        VLMInteg["VLM integration via HF"]
        MultiSample["Multi-sample registration"]
    end
    
    subgraph Phase2["Phase 2: Growth"]
        LoadBal["Load balancer (Nginx)"]
        MultiServ["Multi-server backend"]
        Redis["Redis cache layer"]
        CloudS3["Cloud storage (S3)"]
        VideoCache["Video processing cache"]
    end
    
    subgraph Phase3["Phase 3: Enterprise"]
        K8s["Kubernetes orchestration"]
        DBShard["Database sharding"]
        EdgeAI["Edge computing<br/>(face recognition)"]
        WebSocket["Real-time WebSocket"]
        MsgQueue["Message queue<br/>(Kafka/RabbitMQ)"]
        Monitoring["Advanced monitoring<br/>(Prometheus/Grafana)"]
    end
    
    Phase1 -->|Scale up| Phase2
    Phase2 -->|Distribute| Phase3
    
    style Phase1 fill:#c8e6c9
    style Phase2 fill:#fff9c4
    style Phase3 fill:#f8bbd0
```

---

## Summary of Changes (v2.0+)

**New Components:**
✅ Registration Session Manager (in-memory with timeout)
✅ Multi-sample face embedding aggregation
✅ Video face recognition module with frame sampling
✅ VLM integration (Qwen via HuggingFace)
✅ CSV-based embedding persistence
✅ Image resizing for VLM optimization

**New Endpoints (5 added):**
- `/api/workers/register/start`
- `/api/workers/register/capture`
- `/api/workers/register/complete`
- `/api/ask-vlm`
- `/api/manager/signup` & `/api/manager/login` (alternatives)

**Enhanced Workflows:**
- Face detection now feeds into VLM reasoning
- Registration now collects multiple samples for better accuracy
- Video uploads analyzed with frame voting
- Detector facts (JSON) injected into VLM prompts
