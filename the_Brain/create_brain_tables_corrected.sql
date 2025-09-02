-- Brain Database Schema - CORRECTED VERSION
-- Each table contains ALL core convention fields + category-specific fields

-- 1. Context Table (reusable context referenced by context_id)
CREATE TABLE IF NOT EXISTS contexts (
    id VARCHAR PRIMARY KEY,
    situation JSONB, -- {activity, goal, task_in_focus, mental_load}
    social JSONB, -- {alone, with, roles}
    environment JSONB, -- {indoor/outdoor, noise, light, temperature_c, weather_id, ambience_notes}
    sensory_cues JSONB, -- {smell, color_palette, music, objects_in_view}
    physiology JSONB, -- {fatigue, hunger, pain}
    devices JSONB, -- {device_id, app, os, location_permission}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Person entities (ALL core fields + person-specific fields)
CREATE TABLE IF NOT EXISTS persons (
    -- CORE CONVENTION FIELDS (in every table)
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'person' CHECK (type = 'person'),
    title VARCHAR NOT NULL,
    aliases TEXT[], -- Array of alternative names
    summary TEXT,
    embedding_refs JSONB, -- {text: id, image: id, audio: id}
    time_info JSONB, -- {start, end, duration_s, detected_granularity}
    location_info JSONB, -- {geo: {lat, lon, geohash}, address, place_id}
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB, -- {valence, arousal, label}
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB, -- {origin, url, file_id, extractor}
    provenance JSONB, -- {created_at, updated_at, observed_at, created_by}
    privacy_info JSONB, -- {level, retention, pii}
    links JSONB, -- {related_to: [], caused_by: [], causes: [], part_of: [], etc.}
    access_info JSONB, -- {last_accessed_at, access_count}
    
    -- PERSON-SPECIFIC FIELDS
    names JSONB, -- {given, family, full, display}
    pronouns VARCHAR,
    birthdate DATE,
    age_range VARCHAR,
    photos TEXT[], -- Array of image_ids
    faceprint_id VARCHAR, -- Vector reference
    voiceprint_id VARCHAR, -- Vector reference
    contact JSONB, -- {emails, phones, handles, websites}
    timezone VARCHAR,
    home_base_place_id VARCHAR,
    roles JSONB, -- {relationship, title, org_id}
    relationship_strength FLOAT CHECK (relationship_strength >= 0 AND relationship_strength <= 1),
    first_met_event_id VARCHAR,
    met_at_place_id VARCHAR,
    affiliations TEXT[], -- Array of org_ids
    skills_interests JSONB, -- [{topic, level, evidence}]
    preferences JSONB, -- [{domain, like/dislike, notes}]
    important_dates JSONB, -- [{label, date}]
    availability_pattern JSONB, -- {days, hours}
    boundaries JSONB, -- {do_not, sensitive_topics}
    last_contacted_at TIMESTAMP,
    promises JSONB, -- [{what, due, status}]
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Organization entities
CREATE TABLE IF NOT EXISTS organizations (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'organization' CHECK (type = 'organization'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- ORGANIZATION-SPECIFIC FIELDS
    legal_name VARCHAR,
    aka VARCHAR,
    org_type VARCHAR CHECK (org_type IN ('company', 'school', 'nonprofit', 'clinic', 'insurer')),
    domain VARCHAR,
    identifiers JSONB, -- {tax_id, npi, lei}
    hq_place_id VARCHAR,
    locations TEXT[], -- Array of place_ids
    people JSONB, -- [{person_id, role}]
    products_services JSONB, -- [{name, category}]
    relations JSONB, -- {subsidiary_of, partners, competitors}
    policies JSONB, -- [{subject, url}]
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Place entities
CREATE TABLE IF NOT EXISTS places (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'place' CHECK (type = 'place'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- PLACE-SPECIFIC FIELDS
    kind VARCHAR CHECK (kind IN ('home', 'office', 'cafe', 'hospital', 'park', 'city', 'country')),
    geo JSONB, -- {lat, lon, geohash, bbox}
    address TEXT,
    timezone VARCHAR,
    owner_org_id VARCHAR,
    owner_person_id VARCHAR,
    amenities JSONB, -- {wifi, outlets, seating, accessibility}
    opening_hours JSONB,
    noise VARCHAR,
    crowding VARCHAR,
    safety VARCHAR,
    price_level VARCHAR,
    memories_here TEXT[], -- Array of event_ids
    photos TEXT[], -- Array of image_ids
    map_links TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Event entities
CREATE TABLE IF NOT EXISTS events (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'event' CHECK (type = 'event'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- EVENT-SPECIFIC FIELDS
    event_type VARCHAR CHECK (event_type IN ('meeting', 'call', 'trip', 'purchase', 'medical', 'milestone', 'accident', 'celebration', 'deadline')),
    time_details JSONB, -- {start, end, duration_s, recurrence_id}
    location JSONB, -- {place_id}
    participants JSONB, -- [{person_id/org_id, role}]
    influencers TEXT[], -- Array of person_ids
    agenda TEXT,
    actions TEXT,
    decisions TEXT,
    artifacts TEXT[], -- Array of doc_id, media_id, object_id
    costs JSONB, -- [{amount, currency, payer_id, receipt_media_id}]
    transport JSONB, -- {mode, segments}
    weather_id VARCHAR,
    photos TEXT[],
    transcript_id VARCHAR,
    sentiment VARCHAR,
    stress FLOAT CHECK (stress >= 0 AND stress <= 1),
    surprise FLOAT CHECK (surprise >= 0 AND surprise <= 1),
    outcome JSONB, -- {success, notes}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Conversation/Message entities
CREATE TABLE IF NOT EXISTS conversations (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'conversation' CHECK (type = 'conversation'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- CONVERSATION-SPECIFIC FIELDS
    channel VARCHAR CHECK (channel IN ('chat', 'email', 'sms', 'call', 'meeting_notes')),
    thread_id VARCHAR,
    message_id VARCHAR,
    participants TEXT[], -- Array of person_ids
    time_details JSONB, -- {sent_at, received_at}
    content_text_id VARCHAR,
    topics TEXT[],
    entities TEXT[], -- Array of entity_ids
    tone_sentiment VARCHAR,
    toxicity_flag BOOLEAN,
    action_items JSONB, -- [{what, owner_id, due, status}]
    commitments JSONB, -- [{promisor_id, promise, due}]
    attachments TEXT[], -- Array of media_id/doc_id
    followups_event_id VARCHAR,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Task/Goal entities
CREATE TABLE IF NOT EXISTS tasks (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'task' CHECK (type = 'task'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- TASK-SPECIFIC FIELDS
    kind VARCHAR CHECK (kind IN ('task', 'habit', 'goal', 'wishlist')),
    status VARCHAR CHECK (status IN ('todo', 'doing', 'blocked', 'done')),
    priority FLOAT CHECK (priority >= 0 AND priority <= 1),
    urgency FLOAT CHECK (urgency >= 0 AND urgency <= 1),
    value FLOAT CHECK (value >= 0 AND value <= 1),
    owner_id VARCHAR,
    stakeholders TEXT[], -- Array of person_ids
    due_at TIMESTAMP,
    estimate_hours FLOAT,
    actual_hours FLOAT,
    acceptance_criteria TEXT,
    dependencies TEXT[], -- Array of task_ids
    evidence_of_done TEXT[], -- Array of event_id/doc_id
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Project entities
CREATE TABLE IF NOT EXISTS projects (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'project' CHECK (type = 'project'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- PROJECT-SPECIFIC FIELDS
    objective TEXT,
    scope TEXT,
    success_metrics TEXT,
    timeframe JSONB, -- {start, target_end}
    milestones JSONB, -- [{name, due, status}]
    risks JSONB, -- [{risk, likelihood, impact, mitigation}]
    resources JSONB, -- [{repo_url, env, dataset_id}]
    stakeholders JSONB, -- [{person_id, role}]
    decision_log JSONB, -- [{date, decision, rationale, by_id}]
    budget JSONB, -- {planned, actual, currency}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Object/Artifact entities
CREATE TABLE IF NOT EXISTS objects (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'object' CHECK (type = 'object'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- OBJECT-SPECIFIC FIELDS
    category VARCHAR CHECK (category IN ('tool', 'device', 'furniture', 'vehicle', 'paper', 'clothing')),
    make_model VARCHAR,
    serial VARCHAR,
    specs TEXT,
    acquired JSONB, -- {date, price, seller_id, txn_id}
    owner_id VARCHAR,
    current_location_place_id VARCHAR,
    condition VARCHAR,
    last_service_at TIMESTAMP,
    warranty_until DATE,
    manual_doc_id VARCHAR,
    photos TEXT[],
    usage_history TEXT[], -- Array of event_ids
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Media/Document entities
CREATE TABLE IF NOT EXISTS media_documents (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'media' CHECK (type = 'media'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- MEDIA-SPECIFIC FIELDS
    media_type VARCHAR CHECK (media_type IN ('pdf', 'image', 'audio', 'video', 'note', 'webpage', 'slide', 'code')),
    author_ids TEXT[],
    source_url TEXT,
    file_id VARCHAR,
    hash VARCHAR,
    created_at_media TIMESTAMP,
    modified_at_media TIMESTAMP,
    summary_text_id VARCHAR,
    key_quotes JSONB, -- [{text_span}]
    claims JSONB, -- [{claim, stance, source_doc_id}]
    topics TEXT[],
    entities TEXT[],
    reading_progress JSONB, -- {percent, last_opened_at}
    rights_license TEXT,
    share_with TEXT[], -- Array of person_ids
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Idea/Concept entities
CREATE TABLE IF NOT EXISTS ideas (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'idea' CHECK (type = 'idea'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- IDEA-SPECIFIC FIELDS
    definition TEXT,
    analogy TEXT,
    counterexample TEXT,
    category VARCHAR CHECK (category IN ('theory', 'pattern', 'heuristic', 'design')),
    examples TEXT[], -- Array of event_id/doc_id
    related_concepts TEXT[], -- Array of concept_ids
    open_questions TEXT[],
    applications TEXT[], -- Array of project_id/task_id
    understanding_level FLOAT CHECK (understanding_level >= 0 AND understanding_level <= 1),
    confusion_points TEXT[],
    origin JSONB, -- {inspired_by: [doc_id/person_id/event_id]}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Knowledge/Fact entities
CREATE TABLE IF NOT EXISTS knowledge_facts (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'knowledge' CHECK (type = 'knowledge'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- KNOWLEDGE-SPECIFIC FIELDS
    triple JSONB, -- {subject_id/text, predicate, object_id/text}
    scope VARCHAR CHECK (scope IN ('personal', 'world', 'work')),
    valid_time JSONB, -- {start, end}
    certainty FLOAT CHECK (certainty >= 0 AND certainty <= 1),
    source_doc_id VARCHAR,
    citation TEXT,
    derivations TEXT[], -- Array of fact_ids
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Preference entities
CREATE TABLE IF NOT EXISTS preferences (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'preference' CHECK (type = 'preference'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- PREFERENCE-SPECIFIC FIELDS
    domain VARCHAR CHECK (domain IN ('food', 'music', 'work', 'travel', 'communication', 'shopping', 'health')),
    item TEXT,
    like_level FLOAT CHECK (like_level >= 0 AND like_level <= 1),
    avoid_level FLOAT CHECK (avoid_level >= 0 AND avoid_level <= 1),
    constraints TEXT, -- allergies, ethics, budget, time
    evidence TEXT[], -- Array of event_id/doc_id
    stability FLOAT CHECK (stability >= 0 AND stability <= 1),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Routine/Habit entities
CREATE TABLE IF NOT EXISTS routines (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'routine' CHECK (type = 'routine'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- ROUTINE-SPECIFIC FIELDS
    behavior TEXT,
    cue JSONB, -- {time_of_day, place_id, emotion}
    frequency JSONB, -- {per_week, schedule}
    streak_days INTEGER,
    compliance_rate FLOAT CHECK (compliance_rate >= 0 AND compliance_rate <= 1),
    reward TEXT,
    costs JSONB, -- {time, money, energy}
    replacement_behavior TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Health Episode entities
CREATE TABLE IF NOT EXISTS health_episodes (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'health' CHECK (type = 'health'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- HEALTH-SPECIFIC FIELDS
    symptoms JSONB, -- [{name, severity, onset_at, duration}]
    triggers TEXT[], -- Array of event_id/food/place_id/weather_id
    reliefs TEXT[], -- Array of medication_id/behavior
    diagnoses JSONB, -- [{dx, provider_id, date}]
    medications JSONB, -- [{drug, dose, schedule}]
    vitals_labs JSONB, -- [{name, value, unit, date}]
    care_events TEXT[], -- Array of event_ids
    insurer_info JSONB, -- {payer_org_id, claim_id, cost}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. Travel/Trip entities
CREATE TABLE IF NOT EXISTS travels (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'travel' CHECK (type = 'travel'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- TRAVEL-SPECIFIC FIELDS
    purpose VARCHAR CHECK (purpose IN ('work', 'vacation', 'family')),
    segments JSONB, -- [{mode, start_place_id, end_place_id, depart_at, arrive_at, provider_org_id}]
    lodging JSONB, -- {place_id, check_in, check_out, conf_code}
    companions TEXT[], -- Array of person_ids
    itinerary_doc_id VARCHAR,
    tickets_media_ids TEXT[],
    budget_vs_actual JSONB,
    photos TEXT[],
    memorable_events TEXT[], -- Array of event_ids
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 17. Transaction entities
CREATE TABLE IF NOT EXISTS transactions (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'transaction' CHECK (type = 'transaction'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- TRANSACTION-SPECIFIC FIELDS
    txn_type VARCHAR CHECK (txn_type IN ('purchase', 'sale', 'transfer', 'subscription', 'donation', 'refund')),
    dt TIMESTAMP,
    amount DECIMAL(15,2),
    currency VARCHAR(3),
    counterparty_id VARCHAR,
    method VARCHAR CHECK (method IN ('card', 'cash', 'bank', 'crypto')),
    items JSONB, -- [{object_id/desc, qty, unit_price}]
    category VARCHAR CHECK (category IN ('groceries', 'tools', 'healthcare', 'travel', 'rent', 'income')),
    receipt_media_id VARCHAR,
    warranty_until DATE,
    linked_event_id VARCHAR,
    budget_bucket VARCHAR,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 18. Device/App Session entities
CREATE TABLE IF NOT EXISTS device_sessions (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'device_session' CHECK (type = 'device_session'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- DEVICE SESSION-SPECIFIC FIELDS
    device_id VARCHAR,
    device_kind VARCHAR,
    os_version VARCHAR,
    app_id VARCHAR,
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    activity JSONB, -- [{event, payload_ids}]
    notifications_count INTEGER,
    focus_mode BOOLEAN,
    privacy_shared JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 19. Time Period entities
CREATE TABLE IF NOT EXISTS time_periods (
    -- CORE CONVENTION FIELDS
    id VARCHAR PRIMARY KEY,
    type VARCHAR DEFAULT 'time_period' CHECK (type = 'time_period'),
    title VARCHAR NOT NULL,
    aliases TEXT[],
    summary TEXT,
    embedding_refs JSONB,
    time_info JSONB,
    location_info JSONB,
    context_id VARCHAR REFERENCES contexts(id),
    tags TEXT[],
    salience FLOAT CHECK (salience >= 0 AND salience <= 1),
    emotion JSONB,
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    source_info JSONB,
    provenance JSONB,
    privacy_info JSONB,
    links JSONB,
    access_info JSONB,
    
    -- TIME PERIOD-SPECIFIC FIELDS
    label VARCHAR,
    time_range JSONB, -- {start, end}
    theme VARCHAR CHECK (theme IN ('work', 'health', 'travel', 'family', 'learning')),
    signature_events TEXT[], -- Array of event_ids
    dominant_emotion VARCHAR,
    highlights TEXT,
    lowlights TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_persons_type ON persons(type);
CREATE INDEX IF NOT EXISTS idx_persons_created_at ON persons(created_at);
CREATE INDEX IF NOT EXISTS idx_persons_tags ON persons USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_persons_salience ON persons(salience);
CREATE INDEX IF NOT EXISTS idx_persons_relationship_strength ON persons(relationship_strength);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_tags ON events USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(type);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_dt ON transactions(dt);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);