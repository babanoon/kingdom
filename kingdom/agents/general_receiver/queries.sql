-- GeneralReceiver Agent - SQL Queries
-- Database queries for conversation logging, analytics, and data management

-- Create conversation logging table
CREATE TABLE IF NOT EXISTS conversation_logs (
    id SERIAL PRIMARY KEY,
    conversation_id UUID DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,
    sender VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    forum VARCHAR(100),
    workflow_id VARCHAR(100),
    routed BOOLEAN DEFAULT FALSE,
    target_agent VARCHAR(50),
    processing_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create routing decisions table
CREATE TABLE IF NOT EXISTS routing_decisions (
    id SERIAL PRIMARY KEY,
    conversation_id UUID,
    agent_id VARCHAR(50) NOT NULL,
    original_message TEXT NOT NULL,
    routing_category VARCHAR(50),
    target_agent VARCHAR(50),
    confidence_score DECIMAL(3,2),
    keywords_matched TEXT[],
    decision_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create agent performance metrics table
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data JSONB
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_logs_agent_id ON conversation_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_conversation_logs_timestamp ON conversation_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_logs_workflow ON conversation_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_routing_decisions_agent ON routing_decisions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_time ON agent_metrics(agent_id, metric_timestamp);

-- =====================================
-- Query Templates for GeneralReceiver
-- =====================================

-- Log a conversation interaction
-- Usage: Replace placeholders with actual values
INSERT INTO conversation_logs (
    conversation_id, agent_id, sender, message, response, 
    forum, workflow_id, routed, target_agent, processing_time_ms, confidence_score
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
);

-- Log a routing decision
INSERT INTO routing_decisions (
    conversation_id, agent_id, original_message, routing_category,
    target_agent, confidence_score, keywords_matched
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
);

-- Log agent performance metric
INSERT INTO agent_metrics (
    agent_id, metric_name, metric_value, additional_data
) VALUES (
    %s, %s, %s, %s
);

-- =====================================
-- Analytical Queries
-- =====================================

-- Get conversation history for a specific agent
SELECT 
    conversation_id,
    sender,
    message,
    response,
    forum,
    routed,
    target_agent,
    processing_time_ms,
    created_at
FROM conversation_logs 
WHERE agent_id = %s
ORDER BY created_at DESC
LIMIT %s;

-- Get routing statistics for an agent
SELECT 
    routing_category,
    target_agent,
    COUNT(*) as routing_count,
    AVG(confidence_score) as avg_confidence,
    array_agg(DISTINCT unnest(keywords_matched)) as all_keywords
FROM routing_decisions 
WHERE agent_id = %s
    AND decision_timestamp >= %s
GROUP BY routing_category, target_agent
ORDER BY routing_count DESC;

-- Get agent performance summary
SELECT 
    agent_id,
    COUNT(*) as total_conversations,
    AVG(processing_time_ms) as avg_processing_time,
    COUNT(CASE WHEN routed = TRUE THEN 1 END) as routed_conversations,
    COUNT(CASE WHEN routed = FALSE THEN 1 END) as direct_responses,
    AVG(confidence_score) as avg_confidence
FROM conversation_logs
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY agent_id;

-- Get hourly conversation volume
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as conversation_count,
    AVG(processing_time_ms) as avg_processing_time
FROM conversation_logs
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour;

-- Get most common conversation topics (based on routing)
SELECT 
    COALESCE(routing_category, 'general') as topic,
    COUNT(*) as frequency,
    AVG(processing_time_ms) as avg_processing_time
FROM conversation_logs cl
LEFT JOIN routing_decisions rd ON cl.conversation_id = rd.conversation_id
WHERE cl.agent_id = %s
    AND cl.created_at >= %s
GROUP BY COALESCE(routing_category, 'general')
ORDER BY frequency DESC;

-- Get recent errors or issues
SELECT 
    conversation_id,
    sender,
    message,
    response,
    processing_time_ms,
    created_at
FROM conversation_logs
WHERE agent_id = %s
    AND (
        response LIKE '%error%' OR 
        response LIKE '%sorry%' OR 
        processing_time_ms > 10000
    )
    AND created_at >= %s
ORDER BY created_at DESC
LIMIT 20;

-- =====================================
-- Maintenance Queries
-- =====================================

-- Clean old conversation logs (older than 30 days)
DELETE FROM conversation_logs 
WHERE created_at < NOW() - INTERVAL '30 days';

-- Clean old routing decisions (older than 30 days)
DELETE FROM routing_decisions 
WHERE decision_timestamp < NOW() - INTERVAL '30 days';

-- Clean old metrics (older than 7 days)
DELETE FROM agent_metrics 
WHERE metric_timestamp < NOW() - INTERVAL '7 days';

-- Update table statistics for query optimization
ANALYZE conversation_logs;
ANALYZE routing_decisions;
ANALYZE agent_metrics;

-- =====================================
-- Monitoring Queries
-- =====================================

-- Check agent health metrics
SELECT 
    agent_id,
    metric_name,
    metric_value,
    metric_timestamp
FROM agent_metrics
WHERE agent_id = %s
    AND metric_timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY metric_timestamp DESC;

-- Get current active conversations
SELECT 
    COUNT(*) as active_conversations,
    COUNT(DISTINCT sender) as unique_users,
    AVG(processing_time_ms) as avg_response_time
FROM conversation_logs
WHERE agent_id = %s
    AND created_at >= NOW() - INTERVAL '5 minutes';

-- Check for performance issues
SELECT 
    'high_response_time' as issue_type,
    COUNT(*) as occurrence_count
FROM conversation_logs
WHERE agent_id = %s
    AND processing_time_ms > 5000
    AND created_at >= NOW() - INTERVAL '1 hour'

UNION ALL

SELECT 
    'frequent_routing' as issue_type,
    COUNT(*) as occurrence_count
FROM conversation_logs
WHERE agent_id = %s
    AND routed = TRUE
    AND created_at >= NOW() - INTERVAL '1 hour';