# Abstract Enclave Assessment — Full System Architecture

## System Overview

```mermaid
graph TB
    subgraph Client["Browser Client"]
        UI["Next.js 16 App<br/>React 19 + Tailwind 4"]
        WEBGL["Three.js WebGL<br/>Background Scene"]
        EMOTION["face-api.js<br/>Emotion Detection<br/>client-side only"]
        STATE["SessionContext<br/>useReducer"]
        
        UI --> WEBGL
        UI --> STATE
        UI -.-> EMOTION
    end
    
    subgraph Proxy["Reverse Proxy"]
        NGINX["Nginx<br/>Gzip + CDN Cache<br/>Route Split"]
    end
    
    subgraph Backend["FastAPI Backend"]
        ROUTER["API Routers<br/>sessions / signals /<br/>companion / scoring"]
        
        subgraph Core["Core Module"]
            CONSTRUCTS["Constructs Registry<br/>4 constructs x 4 sub-facets<br/>x 2-3 indicators = 34"]
            INTERACTION["Interaction Loop<br/>FSM + Timing Model"]
            NARRATIVE["Narrative Engine<br/>Chambers + Puzzles"]
            SCORING_MODEL["Scoring Model<br/>Weighted Aggregation"]
        end
        
        subgraph Services["Services"]
            LLM["LLM Gateway<br/>Gemini 2.0 Flash<br/>+ Rule Fallback"]
            ADAPTIVE["Adaptive Engine<br/>epsilon-greedy + ELO"]
            EMOTION_SVC["Emotion Aggregator<br/>Valence-Arousal"]
            EXPLAIN["Explainability<br/>SHAP-inspired"]
            PIPELINE["Event Pipeline<br/>Feature Extraction"]
            BAYESIAN["Bayesian Scoring<br/>Beta Posteriors"]
        end
        
        subgraph Engine["Game Engine"]
            SM["State Machine<br/>Event Bus + Pub/Sub"]
            NARR_CTRL["Narrative Controller<br/>Branching Logic"]
            LATIN["Latin Square<br/>Counterbalancing"]
        end
        
        subgraph Calibration["Calibration"]
            VALIDITY["Convergent Validity<br/>BFI / CEI / PANAS / NEO"]
            FAIRNESS["Fairness Audit<br/>DIF + Demographic Parity"]
        end
        
        subgraph Monitoring["Monitoring"]
            METRICS["MetricsCollector<br/>Counters / Gauges / Histograms"]
            ANALYTICS["AnalyticsTracker<br/>Session Lifecycle"]
        end
        
        ROUTER --> Engine
        ROUTER --> Services
        Engine --> Core
        Services --> Core
    end
    
    subgraph Data["Data Layer"]
        DB[("PostgreSQL 16<br/>Sessions + Signals + Scores")]
        REDIS[("Redis 7<br/>Session Cache")]
    end
    
    subgraph External["External"]
        GEMINI["Google Gemini API<br/>Free Tier"]
    end
    
    Client -->|HTTPS| NGINX
    NGINX -->|"/api/*"| ROUTER
    NGINX -->|"/*"| UI
    Backend --> DB
    Backend --> REDIS
    LLM --> GEMINI
```

---

## Data Flow — Single Assessment Session

```mermaid
sequenceDiagram
    participant U as User Browser
    participant F as Next.js Frontend
    participant N as Nginx
    participant A as FastAPI Backend
    participant L as Gemini LLM
    participant D as PostgreSQL
    
    U->>F: Open application
    F->>F: Render consent screen
    U->>F: Accept consent
    U->>F: Select mode (self-awareness)
    F->>N: POST /api/v1/sessions
    N->>A: Create session
    A->>A: Latin Square - chamber order
    A-->>F: session_id, chamber_order
    
    loop For each chamber (4x)
        F->>F: Show entry narrative (3s)
        
        loop For each interaction (3x)
            F->>F: Display interaction + timer
            U->>F: User responds
            F->>F: Capture events locally
            F->>N: POST /api/v1/signals
            N->>A: Ingest + extract features
            A-->>F: extracted features
            
            opt AI Companion
                F->>N: POST /api/v1/companion/chat
                N->>A: Build prompt
                A->>L: Gemini API call
                L-->>A: Response
                A-->>F: companion response
            end
        end
        
        F->>F: Show exit narrative (2.5s)
    end
    
    F->>N: POST /api/v1/scoring/compute
    N->>A: Bayesian scoring
    A->>A: Score all 4 constructs
    A->>A: Generate explanations
    A->>D: Persist scores
    A-->>F: scores, explanations, CIs
    F->>F: Render results dashboard
```

---

## Module Dependency Graph

```mermaid
graph LR
    subgraph Phase1["Phase 1 - Foundation"]
        C["constructs.py"] --> IL["interaction_loop.py"]
        C --> SM_P1["scoring_model.py"]
        IL --> N["narrative.py"]
    end
    
    subgraph Phase2["Phase 2 - AI"]
        LLM_M["llm_service.py"]
        AE["adaptive_engine.py"]
        ED["emotion_detector.py"]
        EX["explainability.py"]
    end
    
    subgraph Phase3["Phase 3 - Engine"]
        FSM["state_machine.py"]
        DB_M["database.py"]
        EP["event_pipeline.py"]
    end
    
    subgraph Phase4["Phase 4 - Calibration"]
        SE["scoring_engine.py"]
        VA["validity.py"]
        FA["fairness.py"]
    end
    
    C --> EX
    C --> SE
    C --> EP
    SM_P1 --> SE
    IL --> FSM
    N --> FSM
    SE --> EX
```

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 16 (App Router) | Server-side rendering, routing |
| **UI Framework** | React | 19 | Component architecture |
| **Styling** | Tailwind CSS | 4 | Utility-first CSS |
| **3D Graphics** | Three.js / R3F | Latest | Immersive background |
| **Animation** | Framer Motion | Latest | Micro-interactions |
| **Backend** | FastAPI | 0.115+ | Async REST API |
| **ORM** | SQLAlchemy | 2.0 (async) | Database abstraction |
| **Database** | PostgreSQL | 16 | Persistent storage |
| **Cache** | Redis | 7 | Session state caching |
| **AI/LLM** | Google Gemini | 2.0 Flash | Adaptive companion dialogue |
| **Proxy** | Nginx | Latest | Reverse proxy, caching |
| **Container** | Docker | Latest | Deployment orchestration |

---

## Scoring Pipeline Detail

```
Raw Signals (34 behavioral indicators)
    │
    ▼
┌──────────────────────────────┐
│  Feature Extraction          │
│  (EventPipeline)             │
│  click → latency, revision,  │
│  dwell, text, exploration    │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Normalization               │
│  min-max → [0, 1]           │
│  polarity adjustment         │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Weighted Aggregation        │
│  indicator → sub-facet       │
│  sub-facet → construct       │
│  (weighted average)          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Bayesian Posterior Update   │
│  Beta(α₀=2, β₀=2) prior     │
│  + observed evidence         │
│  → 95% credible interval    │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Scale & Report              │
│  [0,1] → [1,10] score       │
│  + explainability layer      │
│  + strengths/growth areas    │
└──────────────────────────────┘
```

---

## Directory Structure

```
FINAL/
├── backend/
│   ├── src/
│   │   ├── core/              # Phase 1: Constructs, FSM, Scoring Model, Narrative
│   │   ├── engine/            # Phase 3: State Machine, Event Bus, Latin Square
│   │   ├── services/          # Phase 2+3: LLM, Adaptive, Emotion, Pipeline, Scoring
│   │   ├── calibration/       # Phase 4: Validity, Fairness
│   │   ├── models/            # Phase 3: SQLAlchemy DB models
│   │   ├── routers/           # Phase 5: API endpoints
│   │   ├── monitoring.py      # Phase 6: Metrics + Analytics
│   │   ├── deployment.py      # Phase 6: Config constants
│   │   └── main.py            # FastAPI app entry point
│   ├── tests/                 # 177 tests (5 test files)
│   └── requirements.txt
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   └── src/
│       ├── components/        # UI components (4 main views)
│       └── lib/               # API client, session context, types
├── docs/                      # 9 READMEs + 6 test reports + architecture
├── Dockerfile                 # Multi-stage build
├── docker-compose.yml         # Full stack orchestration
├── nginx.conf                 # Reverse proxy config
└── README.md                  # Project overview
```
