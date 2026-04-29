# Abstract Enclave Assessment — Full System Architecture

```mermaid
graph TB
    subgraph Client["Browser (Client)"]
        UI[Next.js 16 App<br/>React 19 + Tailwind 4]
        WEBGL[Three.js WebGL<br/>Background Scene]
        EMOTION[face-api.js<br/>Emotion Detection<br/>(client-side only)]
        STATE[SessionContext<br/>useReducer]
        
        UI --> WEBGL
        UI --> STATE
        UI -.-> EMOTION
    end
    
    subgraph Proxy["Reverse Proxy"]
        NGINX[Nginx<br/>Gzip + CDN Cache<br/>Route Split]
    end
    
    subgraph Backend["FastAPI Backend"]
        ROUTER[API Routers<br/>sessions / signals /<br/>companion / scoring]
        
        subgraph Core["Core Module"]
            CONSTRUCTS[Constructs Registry<br/>4 constructs × 4 sub-facets<br/>× 2 indicators = 32]
            INTERACTION[Interaction Loop<br/>FSM + Timing Model]
            NARRATIVE[Narrative Engine<br/>Chambers + Puzzles]
            SCORING_MODEL[Scoring Model<br/>Weighted Aggregation]
        end
        
        subgraph Services["Services"]
            LLM[LLM Gateway<br/>Gemini 2.0 Flash<br/>+ Rule Fallback]
            ADAPTIVE[Adaptive Engine<br/>ε-greedy + ELO]
            EMOTION_SVC[Emotion Aggregator<br/>Valence-Arousal]
            EXPLAIN[Explainability<br/>SHAP-inspired]
            PIPELINE[Event Pipeline<br/>Feature Extraction]
            BAYESIAN[Bayesian Scoring<br/>Beta Posteriors]
        end
        
        subgraph Engine["Game Engine"]
            SM[State Machine<br/>Event Bus + Pub/Sub]
            NARR_CTRL[Narrative Controller<br/>Branching Logic]
            LATIN[Latin Square<br/>Counterbalancing]
        end
        
        subgraph Calibration["Calibration"]
            VALIDITY[Convergent Validity<br/>BFI/CEI/PANAS/NEO]
            FAIRNESS[Fairness Audit<br/>DIF + Demographic Parity]
        end
        
        subgraph Monitoring["Monitoring"]
            METRICS[MetricsCollector<br/>Counters/Gauges/Histograms]
            ANALYTICS[AnalyticsTracker<br/>Session Lifecycle]
        end
        
        ROUTER --> Engine
        ROUTER --> Services
        Engine --> Core
        Services --> Core
    end
    
    subgraph Data["Data Layer"]
        DB[(PostgreSQL 16<br/>Sessions + Signals + Scores)]
        REDIS[(Redis 7<br/>Session Cache)]
    end
    
    subgraph External["External"]
        GEMINI[Google Gemini API<br/>Free Tier]
    end
    
    Client -->|HTTPS| NGINX
    NGINX -->|/api/*| ROUTER
    NGINX -->|/*| UI
    Backend --> DB
    Backend --> REDIS
    LLM --> GEMINI
```

## Data Flow (Single Assessment Session)

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
    A->>A: Latin Square → chamber order
    A-->>F: {session_id, chamber_order}
    
    loop For each chamber (4×)
        F->>F: Show entry narrative (3s)
        
        loop For each interaction (3×)
            F->>F: Display interaction + timer
            U->>F: User responds
            F->>F: Capture events locally
            F->>N: POST /api/v1/signals
            N->>A: Ingest + extract features
            A-->>F: {extracted features}
            
            opt AI Companion
                F->>N: POST /api/v1/companion/chat
                N->>A: Build prompt
                A->>L: Gemini API call
                L-->>A: Response
                A-->>F: {companion response}
            end
        end
        
        F->>F: Show exit narrative (2.5s)
    end
    
    F->>N: POST /api/v1/scoring/compute
    N->>A: Bayesian scoring
    A->>A: Score all 4 constructs
    A->>A: Generate explanations
    A->>D: Persist scores
    A-->>F: {scores, explanations, CIs}
    F->>F: Render results dashboard
```

## Module Dependency Graph

```mermaid
graph LR
    subgraph Phase1["Phase 1: Foundation"]
        C[constructs.py] --> IL[interaction_loop.py]
        C --> SM[scoring_model.py]
        IL --> N[narrative.py]
    end
    
    subgraph Phase2["Phase 2: AI"]
        LLM[llm_service.py]
        AE[adaptive_engine.py]
        ED[emotion_detector.py]
        EX[explainability.py]
    end
    
    subgraph Phase3["Phase 3: Engine"]
        FSM[state_machine.py]
        DB[database.py]
        EP[event_pipeline.py]
    end
    
    subgraph Phase4["Phase 4: Calibration"]
        SE[scoring_engine.py]
        VA[validity.py]
        FA[fairness.py]
    end
    
    C --> EX
    C --> SE
    C --> EP
    SM --> SE
    IL --> FSM
    N --> FSM
    SE --> EX
```
