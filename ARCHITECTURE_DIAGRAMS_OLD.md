# VINIMI Architecture - Mermaid Diagrams

## System Architecture Diagram

```mermaid
graph TB
    User["👤 User<br/>Browser"]
    
    subgraph Frontend["🎨 Frontend Layer (React + Vite)"]
        Home["🏠 Home"]
        Auth["🔐 Auth<br/>Login/Signup"]
        Dashboard["📊 Dashboard"]
        Workers["👥 Workers<br/>List & Details"]
        Live["📹 Live<br/>Monitoring"]
        Violations["⚠️ Violations<br/>History"]
        Alerts["🔔 Recent<br/>Alerts"]
        Account["⚙️ Account<br/>Settings"]
    end
    
    subgraph Backend["⚙️ Backend Layer (FastAPI)"]
        Routes["🌐 API Routes<br/>20+ endpoints"]
        Auth_BE["🔐 Auth<br/>Manager Login"]
        Workers_BE["👥 Worker<br/>Management"]
        Detection["🎯 Detection<br/>Orchestration"]
        Tasks["📋 Background<br/>Tasks"]
    end
    
    subgraph AI["🧠 AI/ML Services"]
        YOLO["🔍 YOLO v8<br/>Helmet Detection"]
        DeepFace["👤 DeepFace<br/>Face Recognition"]
        Gallery["📚 Face Gallery<br/>Vector Search"]
    end
    
    subgraph Storage["💾 Storage Layer"]
        MySQL["🗄️ MySQL<br/>vinimi_local"]
        FileSystem["📁 File System<br/>Images/Logs"]
    end
    
    External["🚀 External<br/>Twilio SMS"]
    
    User -->|HTTP/REST| Frontend
    Frontend -->|API Calls| Backend
    Backend -->|Query| Routes
    Routes -->|Process| Auth_BE
    Routes -->|Manage| Workers_BE
    Routes -->|Analyze| Detection
    Routes -->|Async| Tasks
    
    Detection -->|Detect| YOLO
    Detection -->|Extract| DeepFace
    Detection -->|Search| Gallery
    Gallery -->|Load| MySQL
    
    Tasks -->|SMS| External
    Tasks -->|Store| FileSystem
    
    Backend -->|Read/Write| MySQL
    Backend -->|Save| FileSystem
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style AI fill:#f3e5f5
    style Storage fill:#e8f5e9
```

---

## Data Flow Diagram

```mermaid
graph LR
    Camera["📹 Camera"]
    Capture["📸 Frame<br/>Capture"]
    API_IN["POST<br/>/api/live/frame"]
    Decode["🔄 Decode<br/>Image"]
    
    YOLO_DET["🔍 YOLO<br/>Detection"]
    Helmets["🪖 Helmets<br/>Detected?"]
    Faces["👤 Faces<br/>Extracted"]
    
    EMBEDDING["🧮 Face<br/>Embedding"]
    SEARCH["🔎 Search<br/>Gallery"]
    MATCH{"Match<br/>Found?"}
    
    VIOLATION{"Helmet<br/>Violation?"}
    RECORD["📝 Record<br/>Violation"]
    SMS["📱 Send<br/>SMS Alert"]
    LOG["📋 Log<br/>Event"]
    
    RESPONSE["📤 Response<br/>to Frontend"]
    RENDER["🎨 Render<br/>UI Update"]
    
    Camera --> Capture
    Capture --> API_IN
    API_IN --> Decode
    Decode --> YOLO_DET
    YOLO_DET --> Helmets
    Decode --> Faces
    Faces --> EMBEDDING
    EMBEDDING --> SEARCH
    SEARCH --> MATCH
    
    MATCH -->|Yes| VIOLATION
    MATCH -->|No| RECORD
    HELMETS -->|No| VIOLATION
    HELMETS -->|Yes| RESPONSE
    
    VIOLATION -->|True| RECORD
    VIOLATION -->|False| RESPONSE
    
    RECORD --> SMS
    RECORD --> LOG
    SMS --> LOG
    LOG --> RESPONSE
    
    RESPONSE --> RENDER
    RENDER -->|Canvas| Camera
    
    style Camera fill:#ffcccc
    style YOLO_DET fill:#fff9c4
    style MATCH fill:#ffe082
    style VIOLATION fill:#ffccbc
    style SMS fill:#ff9999
    style RENDER fill:#c8e6c9
```

---

## API Endpoint Map

```mermaid
graph TB
    API["FastAPI<br/>http://localhost:8001"]
    
    subgraph Auth["🔐 Authentication"]
        LOGIN["POST /auth/login"]
        SIGNUP["POST /auth/signup"]
        LOGOUT["POST /auth/logout"]
    end
    
    subgraph Workers["👥 Workers"]
        LIST_W["GET /api/workers"]
        GET_W["GET /api/workers/{id}"]
        REGISTER_W["POST /api/workers/register"]
        MEDIA_W["GET /api/workers/{id}/media"]
        VIOLATIONS_W["GET /api/workers/{id}/violations"]
    end
    
    subgraph Detection["🎯 Detection"]
        DETECT["POST /api/detect/frame"]
        LIVE["POST /api/live/frame"]
        ALERTS["GET /api/live/recent-alerts"]
    end
    
    subgraph Violations["⚠️ Violations"]
        LIST_V["GET /api/violations"]
        TEST_ALERT["POST /api/alerts/test"]
        SUMMARY["GET /api/alerts/summary"]
    end
    
    subgraph Logs["📋 Logs"]
        LIST_L["GET /api/logs/list"]
        TAIL_L["GET /api/logs/tail"]
        TODAY_L["GET /api/logs/today"]
        PDF_L["GET /api/logs/today.pdf"]
        DL_L["GET /api/logs/download"]
    end
    
    subgraph Manager["👤 Manager"]
        GET_M["GET /api/manager/{id}"]
        UPDATE_M["PUT /api/manager/{id}"]
    end
    
    Health["GET /health"]
    
    API --> Auth
    API --> Workers
    API --> Detection
    API --> Violations
    API --> Logs
    API --> Manager
    API --> Health
    
    style API fill:#ffe0b2
    style Auth fill:#c8e6c9
    style Workers fill:#bbdefb
    style Detection fill:#f8bbd0
    style Violations fill:#ffe0b2
    style Logs fill:#e1bee7
    style Manager fill:#b2dfdb
```

---

## Frontend Page Navigation

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
        Violations_Page["​/violations → Violations.tsx<br/>Violation History"]
        Recent["​/recent-alerts → RecentAlerts.tsx<br/>Recent SMS Alerts"]
        Account_Page["​/account → Account.tsx<br/>Profile Settings"]
        AskVLM["​/ask → AskVLM.tsx<br/>AI Q&A"]
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
```

---

## Database Schema Diagram (ER Model)

```mermaid
erDiagram
    COMPANY ||--o{ LOCATION : has
    COMPANY ||--o{ MANAGER : has
    COMPANY ||--o{ WORKER : has
    LOCATION ||--o{ WORKER : contains
    WORKER ||--o{ EMBEDDINGS : has
    WORKER ||--o{ WORKER_IMAGE : has
    WORKER ||--o{ VIOLATION : experienced
    VIOLATION ||--o{ ALERTS : triggers
    
    COMPANY {
        int id PK
        string name
        timestamp created_at
    }
    
    LOCATION {
        int id PK
        int company_id FK
        string name
        string address
        timestamp created_at
    }
    
    MANAGER {
        int id PK
        int company_id FK
        string email
        string name
        string password_hash
        timestamp created_at
    }
    
    WORKER {
        int id PK
        int company_id FK
        int location_id FK
        string name
        string phone
        string department
        string shift
        timestamp created_at
    }
    
    EMBEDDINGS {
        int id PK
        int worker_id FK
        string filename
        longtext embedding "JSON vector"
        string name
        timestamp capture_datetime
    }
    
    WORKER_IMAGE {
        int id PK
        int worker_id FK
        string path
        timestamp captured_at
    }
    
    VIOLATION {
        int id PK
        int worker_id FK
        int location_id FK
        timestamp timestamp
        boolean helmet_on
        boolean is_unknown
        float similarity_score
        string image_path
        string sms_sid
        string sms_status
        json details
        timestamp created_at
    }
    
    ALERTS {
        int id PK
        int violation_id FK
        string phone
        string message
        string status
        timestamp created_at
    }
```

---

## Live Detection Workflow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Browser as Browser<br/>Canvas
    participant Frontend as Frontend<br/>React
    participant Backend as Backend<br/>FastAPI
    participant YOLO as YOLO v8
    participant DeepFace as DeepFace
    participant Gallery as Face Gallery
    participant MySQL as MySQL DB
    participant SMS as Twilio
    
    User->>Frontend: Click "Start Monitoring"
    Frontend->>Browser: requestVideoPermission()
    
    loop Every 500ms
        Browser->>Browser: Capture frame
        Frontend->>Frontend: Convert to Blob
        Frontend->>Backend: POST /api/live/frame
        
        Backend->>YOLO: detect_helmets(frame)
        YOLO-->>Backend: {helmets: [...]}
        
        Backend->>DeepFace: extract_faces(frame)
        DeepFace-->>Backend: {faces: [...], embeddings: [...]}
        
        Backend->>Gallery: search_workers(embeddings)
        Gallery->>MySQL: Query similar workers
        MySQL-->>Gallery: Worker matches
        Gallery-->>Backend: Matched workers
        
        alt Unknown Face
            Backend->>Backend: Log unknown detection
            Backend-->>Frontend: {status: "unknown"}
            Frontend->>User: Show registration prompt
        else Worker Found
            Backend->>MySQL: Check worker details
            MySQL-->>Backend: Worker data
            
            alt No Helmet Detected
                Backend->>MySQL: INSERT violation
                Backend->>SMS: Send alert SMS
                SMS-->>Backend: SMS queued
                Backend->>MySQL: Update SMS SID
            end
        end
        
        Backend-->>Frontend: Detection results JSON
        Frontend->>Browser: Draw bboxes
        Frontend->>User: Display real-time
    end
```

---

## Worker Registration Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Frontend<br/>React
    participant Backend as Backend<br/>FastAPI
    participant DeepFace as DeepFace
    participant FileSystem as File System
    participant MySQL as MySQL
    participant Gallery as Face Gallery
    
    User->>Frontend: Unknown face detected
    Frontend->>User: Show registration modal
    
    User->>Frontend: Enter name, phone, etc.
    User->>Frontend: Submit form
    
    Frontend->>Backend: POST /api/workers/register<br/>(FormData)
    
    Backend->>FileSystem: Save face image
    Backend->>DeepFace: Compute embedding
    DeepFace-->>Backend: Face vector
    
    Backend->>MySQL: INSERT worker
    MySQL-->>Backend: worker_id
    
    Backend->>MySQL: INSERT embedding
    MySQL-->>Backend: OK
    
    Backend->>MySQL: INSERT worker_image
    MySQL-->>Backend: OK
    
    Backend->>Gallery: reload_gallery()
    Gallery->>MySQL: Fetch all embeddings
    MySQL-->>Gallery: Updated vectors
    
    Backend-->>Frontend: Success response
    Frontend->>User: Show toast<br/>"Worker registered!"
    Frontend->>Frontend: Close modal
```

---

## Alert Generation & SMS Flow

```mermaid
sequenceDiagram
    participant Detection as Live Detection<br/>Process
    participant Backend as Backend<br/>FastAPI
    participant DB as MySQL
    participant Cache as Alert Cache<br/>In-Memory
    participant SMS as Twilio<br/>SMS Gateway
    participant Manager as Manager<br/>Phone
    
    Detection->>Detection: Frame analyzed
    Detection->>Backend: No helmet detected
    
    Backend->>DB: Query worker phone
    DB-->>Backend: Phone number
    
    Backend->>DB: Check last alert time
    DB-->>Backend: Last alert (if any)
    
    alt Cooldown active (< 15 min)
        Backend->>DB: Log event (no SMS)
    else Cooldown expired
        Backend->>DB: INSERT violation
        Backend->>Cache: Add to recent alerts
        Backend->>SMS: send_sms(phone, message)
        
        SMS->>SMS: Queue message
        SMS-->>Backend: SMS SID, status=queued
        
        Backend->>DB: UPDATE violation<br/>sms_sid, sms_status
        
        SMS->>Manager: Deliver SMS<br/>"VINIMI Alert:<br/>John Doe - No helmet"
        Manager->>Manager: Receives alert
    end
```

---

## Component Architecture (Frontend)

```mermaid
graph TB
    App["App.tsx<br/>Root Component"]
    
    subgraph Layout["Layout Components"]
        DashboardLayout["DashboardLayout.tsx<br/>Main app wrapper"]
        AppBar["AppBar.tsx<br/>Header + Nav"]
        Sidebar["Sidebar.tsx<br/>Navigation menu"]
    end
    
    subgraph Auth_Components["Auth Components"]
        ProtectedRoute["ProtectedRoute.tsx<br/>Auth guard"]
        Login["Login.tsx<br/>Email/password"]
        Signup["Signup.tsx<br/>Create account"]
    end
    
    subgraph Feature_Components["Feature Components"]
        Dashboard["Dashboard.tsx"]
        Workers["Workers.tsx"]
        WorkerDetail["WorkerDetail.tsx"]
        LiveMon["LiveMonitoring.tsx"]
        Violations["Violations.tsx"]
        RecentAlerts["RecentAlerts.tsx"]
        Account["Account.tsx"]
    end
    
    subgraph Home_Components["Landing Page"]
        Hero["Hero.tsx"]
        Features["Features.tsx"]
        KPIs["KPIs.tsx"]
        HowWorks["HowItWorks.tsx"]
        UseCases["UseCases.tsx"]
        SocialProof["SocialProof.tsx"]
        CTA["FinalCTA.tsx"]
    end
    
    subgraph UI_Components["UI Library<br/>shadcn/ui"]
        Button["button.tsx"]
        Card["card.tsx"]
        Dialog["dialog.tsx"]
        Input["input.tsx"]
        Toast["toast.tsx"]
        More["... 20+ more"]
    end
    
    Hooks["Hooks<br/>use-mobile, use-toast<br/>useSidebar"]
    API["lib/api.ts<br/>API Client<br/>40+ functions"]
    Auth["lib/auth.ts<br/>Auth Helpers"]
    Utils["lib/utils.ts<br/>Utilities"]
    
    App --> Layout
    App --> Auth_Components
    App --> Feature_Components
    App --> Home_Components
    
    Layout --> UI_Components
    Feature_Components --> UI_Components
    Home_Components --> UI_Components
    
    Feature_Components --> Hooks
    Feature_Components --> API
    Auth_Components --> Auth
    Feature_Components --> Utils
    
    style App fill:#fff9c4
    style Layout fill:#c8e6c9
    style Auth_Components fill:#ffccbc
    style Feature_Components fill:#bbdefb
    style Home_Components fill:#f8bbd0
    style UI_Components fill:#e1bee7
```

---

## State Management Flow

```mermaid
graph TB
    User["User Action<br/>Click/Input"]
    
    Component["React Component<br/>State Hook"]
    
    Query["React Query<br/>Cache"]
    
    LocalStorage["localStorage<br/>Auth Token"]
    
    API["Backend API<br/>Fetch"]
    
    Server["Server State<br/>MySQL"]
    
    Render["Re-render<br/>UI Update"]
    
    User -->|Event| Component
    Component -->|useState| Component
    Component -->|useQuery| Query
    Component -->|setItem| LocalStorage
    Component -->|apiFetch| API
    
    Query -->|Cached Data| Component
    LocalStorage -->|Stored Token| API
    API -->|HTTP Request| Server
    Server -->|Response| API
    API -->|Update Cache| Query
    Query -->|New Data| Component
    Component -->|Update State| Render
    Render -->|Display| User
    
    style User fill:#ffcccc
    style Component fill:#fff9c4
    style Query fill:#c8e6c9
    style LocalStorage fill:#bbdefb
    style API fill:#ffe0b2
    style Server fill:#e1bee7
    style Render fill:#f8bbd0
```

---

## Deployment Architecture (Production Ready)

```mermaid
graph TB
    Internet["🌐 Internet"]
    
    subgraph CDN["📡 CDN<br/>Static Assets"]
        Assets["Images, CSS,<br/>JS Bundles"]
    end
    
    subgraph LoadBalancer["⚖️ Load Balancer<br/>Nginx/HAProxy"]
        LB["Port 80/443<br/>SSL/TLS"]
    end
    
    subgraph K8s["☸️ Kubernetes Cluster"]
        subgraph Pods["API Pods<br/>FastAPI x3"]
            API1["Pod 1<br/>Port 8001"]
            API2["Pod 2<br/>Port 8001"]
            API3["Pod 3<br/>Port 8001"]
        end
        
        subgraph Front_Pods["Frontend Pods<br/>Nginx x2"]
            FE1["Pod 1<br/>React SPA"]
            FE2["Pod 2<br/>React SPA"]
        end
    end
    
    subgraph Storage["💾 Storage Layer"]
        MySQL["🗄️ MySQL<br/>Replicated"]
        Redis["🔴 Redis<br/>Cache"]
        S3["☁️ S3<br/>Images/Logs"]
    end
    
    subgraph External["🔗 External"]
        Twilio["Twilio<br/>SMS Gateway"]
    end
    
    Internet --> CDN
    Internet --> LoadBalancer
    LoadBalancer --> Pods
    LoadBalancer --> Front_Pods
    
    Pods --> MySQL
    Pods --> Redis
    Pods --> S3
    Pods --> Twilio
    
    style Internet fill:#ffcccc
    style CDN fill:#fff9c4
    style LoadBalancer fill:#ffe0b2
    style K8s fill:#bbdefb
    style Pods fill:#c8e6c9
    style Front_Pods fill:#f8bbd0
    style Storage fill:#e1bee7
```

---

## Technology Stack Visualization

```mermaid
graph TB
    subgraph Frontend["FRONTEND<br/>React Stack"]
        React["⚛️ React 18"]
        Vite["⚡ Vite Bundler"]
        TS["📘 TypeScript"]
        Tailwind["🎨 Tailwind CSS"]
        ShadCN["🧩 shadcn/ui"]
        RQ["📊 React Query"]
    end
    
    subgraph Backend["BACKEND<br/>Python Stack"]
        FastAPI["⚙️ FastAPI"]
        Uvicorn["🚀 Uvicorn"]
        Pydantic["✓ Pydantic"]
        YOLO["🔍 YOLO v8"]
        DeepFace["👤 DeepFace"]
        OpenCV["📷 OpenCV"]
        Twilio["📱 Twilio SDK"]
    end
    
    subgraph Database["DATABASE<br/>Data Stack"]
        MySQL["🗄️ MySQL 8.x"]
        Redis["🔴 Redis"]
        CSV["📄 CSV Files"]
        NPY["🔢 NPY Arrays"]
    end
    
    subgraph DevOps["DEVOPS<br/>Infrastructure"]
        Docker["🐳 Docker"]
        K8s["☸️ Kubernetes"]
        GitHub["🐙 GitHub Actions"]
        AWS["☁️ AWS/GCP"]
    end
    
    Frontend --> React
    Frontend --> Vite
    Frontend --> TS
    Frontend --> Tailwind
    Frontend --> ShadCN
    Frontend --> RQ
    
    Backend --> FastAPI
    Backend --> Uvicorn
    Backend --> Pydantic
    Backend --> YOLO
    Backend --> DeepFace
    Backend --> OpenCV
    Backend --> Twilio
    
    Database --> MySQL
    Database --> Redis
    Database --> CSV
    Database --> NPY
    
    DevOps --> Docker
    DevOps --> K8s
    DevOps --> GitHub
    DevOps --> AWS
    
    style Frontend fill:#bbdefb
    style Backend fill:#fff9c4
    style Database fill:#e1bee7
    style DevOps fill:#c8e6c9
```

---

## Performance Monitoring Diagram

```mermaid
graph TB
    Metrics["📊 Metrics Collection"]
    
    subgraph App_Metrics["Application Metrics"]
        Response["Response Time<br/>(ms)"]
        Throughput["Throughput<br/>(req/s)"]
        Error["Error Rate<br/>(%))"]
    end
    
    subgraph System_Metrics["System Metrics"]
        CPU["CPU Usage<br/>(%)"]
        Memory["Memory<br/>(MB)"]
        Disk["Disk I/O<br/>(bytes/s)"]
    end
    
    subgraph AI_Metrics["AI Model Metrics"]
        Accuracy["Detection Accuracy<br/>(%)"]
        Latency["Model Latency<br/>(ms)"]
        Throughput_AI["Model Throughput<br/>(frames/s)"]
    end
    
    subgraph Business_Metrics["Business Metrics"]
        Alerts["Alerts Sent<br/>(per day)"]
        Workers["Workers Active<br/>(count)"]
        Compliance["Compliance Rate<br/>(%)"]
    end
    
    Monitoring["📈 Monitoring Dashboard<br/>Grafana/DataDog"]
    Alerting["🔔 Alert Rules<br/>PagerDuty"]
    Logging["📋 Centralized Logs<br/>ELK/Splunk"]
    
    Metrics --> App_Metrics
    Metrics --> System_Metrics
    Metrics --> AI_Metrics
    Metrics --> Business_Metrics
    
    App_Metrics --> Monitoring
    System_Metrics --> Monitoring
    AI_Metrics --> Monitoring
    Business_Metrics --> Monitoring
    
    Monitoring --> Alerting
    Monitoring --> Logging
```

---

## Configuration & Environment Setup

```mermaid
graph TB
    Dev["👨‍💻 Development<br/>Environment"]
    
    subgraph Frontend_Config["Frontend Config"]
        FE_Env["​.env.local<br/>VITE_LIVE_API_URL"]
        FE_Node["node_modules<br/>package.json"]
    end
    
    subgraph Backend_Config["Backend Config"]
        BE_Env["​.env<br/>DB credentials<br/>API keys"]
        Config_Py["config.py<br/>Pydantic Settings"]
        Requirements["requirements.txt<br/>Python packages"]
    end
    
    subgraph Database_Config["Database Setup"]
        SQL_File["vinimi_local_schema.sql<br/>Create tables"]
        CSV_Data["embeddings_with_vectors.csv<br/>Face data"]
        Seed["Seed data<br/>3 companies"]
    end
    
    subgraph File_Structure["File Storage"]
        Images["worker_images/<br/>Face captures"]
        Logs["logs/<br/>Event logs"]
        Models["YOLO models<br/>best.pt"]
    end
    
    Dev --> Frontend_Config
    Dev --> Backend_Config
    Dev --> Database_Config
    Dev --> File_Structure
    
    style Dev fill:#fff9c4
    style Frontend_Config fill:#bbdefb
    style Backend_Config fill:#fff9c4
    style Database_Config fill:#c8e6c9
    style File_Structure fill:#f8bbd0
```

---

## Complete System Interaction Map

```mermaid
graph TB
    Manager["👤 Manager<br/>Portal User"]
    Camera["📹 Security<br/>Camera"]
    
    subgraph App["VINIMI Application"]
        FE["Frontend SPA<br/>React"]
        API["Backend API<br/>FastAPI"]
        AI["AI Services<br/>YOLO+DeepFace"]
        DB["MySQL<br/>Database"]
    end
    
    subgraph Systems["External Systems"]
        SMS["📱 Twilio<br/>SMS Service"]
        Storage["☁️ Cloud Storage<br/>S3"]
    end
    
    Manager -->|Login| FE
    Manager -->|View Data| FE
    Manager -->|Manage Workers| FE
    Manager -->|Receive Alerts| SMS
    
    Camera -->|Continuous Feed| API
    API -->|Process| AI
    AI -->|Query| DB
    API -->|Store| Storage
    API -->|Send Alert| SMS
    
    FE -->|API Calls| API
    FE -->|Fetch| DB
    FE -->|Display| Manager
    
    SMS -->|Notify| Manager
    
    style Manager fill:#ffcccc
    style Camera fill:#fff9c4
    style App fill:#bbdefb
    style Systems fill:#c8e6c9
```
