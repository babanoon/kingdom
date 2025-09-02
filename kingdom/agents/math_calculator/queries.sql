-- MathCalculator Agent - SQL Queries
-- Database queries for mathematical problem logging, solution tracking, and performance analytics

-- Create mathematical solutions table
CREATE TABLE IF NOT EXISTS math_solutions (
    id SERIAL PRIMARY KEY,
    solution_id UUID DEFAULT gen_random_uuid(),
    agent_id VARCHAR(50) NOT NULL,
    problem TEXT NOT NULL,
    problem_type VARCHAR(50),
    complexity_level VARCHAR(20),
    python_code TEXT,
    solution_steps TEXT[],
    final_answer TEXT,
    confidence_score DECIMAL(3,2),
    execution_time_ms INTEGER,
    has_visualization BOOLEAN DEFAULT FALSE,
    visualization_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create problem classifications table
CREATE TABLE IF NOT EXISTS problem_classifications (
    id SERIAL PRIMARY KEY,
    solution_id UUID REFERENCES math_solutions(solution_id),
    agent_id VARCHAR(50) NOT NULL,
    original_problem TEXT NOT NULL,
    classified_type VARCHAR(50),
    confidence_score DECIMAL(3,2),
    keywords_matched TEXT[],
    classification_method VARCHAR(50),
    requires_code BOOLEAN,
    estimated_complexity VARCHAR(20),
    classification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create solution validations table
CREATE TABLE IF NOT EXISTS solution_validations (
    id SERIAL PRIMARY KEY,
    solution_id UUID REFERENCES math_solutions(solution_id),
    validator_agent_id VARCHAR(50) NOT NULL,
    validation_type VARCHAR(50),
    is_correct BOOLEAN,
    validation_confidence DECIMAL(3,2),
    issues_found TEXT[],
    suggestions TEXT[],
    validation_method VARCHAR(100),
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create mathematical concepts usage table
CREATE TABLE IF NOT EXISTS math_concepts_usage (
    id SERIAL PRIMARY KEY,
    solution_id UUID REFERENCES math_solutions(solution_id),
    concept_name VARCHAR(100) NOT NULL,
    concept_category VARCHAR(50),
    usage_frequency INTEGER DEFAULT 1,
    concept_difficulty VARCHAR(20),
    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create agent performance metrics table (extends general metrics)
CREATE TABLE IF NOT EXISTS math_agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL,
    metric_date DATE DEFAULT CURRENT_DATE,
    problems_solved INTEGER DEFAULT 0,
    average_execution_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    accuracy_rate DECIMAL(5,2),
    problems_by_type JSONB,
    visualization_rate DECIMAL(5,2),
    common_errors JSONB,
    performance_trends JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_math_solutions_agent ON math_solutions(agent_id);
CREATE INDEX IF NOT EXISTS idx_math_solutions_type ON math_solutions(problem_type);
CREATE INDEX IF NOT EXISTS idx_math_solutions_timestamp ON math_solutions(created_at);
CREATE INDEX IF NOT EXISTS idx_problem_classifications_type ON problem_classifications(classified_type);
CREATE INDEX IF NOT EXISTS idx_solution_validations_solution ON solution_validations(solution_id);
CREATE INDEX IF NOT EXISTS idx_math_concepts_concept ON math_concepts_usage(concept_name);
CREATE INDEX IF NOT EXISTS idx_math_metrics_agent_date ON math_agent_metrics(agent_id, metric_date);

-- =====================================
-- Query Templates for MathCalculator
-- =====================================

-- Log a mathematical solution
INSERT INTO math_solutions (
    agent_id, problem, problem_type, complexity_level, python_code,
    solution_steps, final_answer, confidence_score, execution_time_ms,
    has_visualization, visualization_data
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
) RETURNING solution_id;

-- Log problem classification
INSERT INTO problem_classifications (
    solution_id, agent_id, original_problem, classified_type,
    confidence_score, keywords_matched, requires_code, estimated_complexity
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
);

-- Log solution validation
INSERT INTO solution_validations (
    solution_id, validator_agent_id, validation_type, is_correct,
    validation_confidence, issues_found, suggestions
) VALUES (
    %s, %s, %s, %s, %s, %s, %s
);

-- Record mathematical concept usage
INSERT INTO math_concepts_usage (
    solution_id, concept_name, concept_category, concept_difficulty
) VALUES (
    %s, %s, %s, %s
)
ON CONFLICT (solution_id, concept_name) 
DO UPDATE SET 
    usage_frequency = math_concepts_usage.usage_frequency + 1,
    last_used = CURRENT_TIMESTAMP;

-- =====================================
-- Analytical Queries
-- =====================================

-- Get solution history for an agent
SELECT 
    ms.solution_id,
    ms.problem,
    ms.problem_type,
    ms.final_answer,
    ms.confidence_score,
    ms.execution_time_ms,
    ms.has_visualization,
    ms.created_at
FROM math_solutions ms
WHERE ms.agent_id = %s
ORDER BY ms.created_at DESC
LIMIT %s;

-- Get problem type distribution
SELECT 
    problem_type,
    COUNT(*) as problem_count,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(confidence_score) as avg_confidence,
    SUM(CASE WHEN has_visualization THEN 1 ELSE 0 END) as visualizations_created
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY problem_type
ORDER BY problem_count DESC;

-- Get agent performance summary
SELECT 
    agent_id,
    COUNT(*) as total_solutions,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(confidence_score) as avg_confidence,
    COUNT(CASE WHEN has_visualization THEN 1 END) as visualizations_created,
    COUNT(DISTINCT problem_type) as problem_types_solved
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY agent_id;

-- Get most common mathematical concepts
SELECT 
    mc.concept_name,
    mc.concept_category,
    SUM(mc.usage_frequency) as total_usage,
    COUNT(DISTINCT ms.solution_id) as problems_used_in,
    AVG(ms.confidence_score) as avg_confidence_when_used
FROM math_concepts_usage mc
JOIN math_solutions ms ON mc.solution_id = ms.solution_id
WHERE ms.agent_id = %s
    AND ms.created_at >= %s
GROUP BY mc.concept_name, mc.concept_category
ORDER BY total_usage DESC
LIMIT 20;

-- Get accuracy trends by validation
SELECT 
    DATE_TRUNC('day', sv.validation_timestamp) as validation_date,
    COUNT(*) as validations_performed,
    SUM(CASE WHEN sv.is_correct THEN 1 ELSE 0 END) as correct_solutions,
    AVG(CASE WHEN sv.is_correct THEN 1.0 ELSE 0.0 END) as accuracy_rate,
    AVG(sv.validation_confidence) as avg_validation_confidence
FROM solution_validations sv
JOIN math_solutions ms ON sv.solution_id = ms.solution_id
WHERE ms.agent_id = %s
    AND sv.validation_timestamp >= %s
GROUP BY DATE_TRUNC('day', sv.validation_timestamp)
ORDER BY validation_date;

-- Get execution time trends
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    problem_type,
    COUNT(*) as problems_solved,
    AVG(execution_time_ms) as avg_execution_time,
    MIN(execution_time_ms) as min_execution_time,
    MAX(execution_time_ms) as max_execution_time
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY DATE_TRUNC('hour', created_at), problem_type
ORDER BY hour, problem_type;

-- Get complex problem analysis
SELECT 
    ms.problem,
    ms.problem_type,
    ms.complexity_level,
    ms.execution_time_ms,
    ms.confidence_score,
    pc.keywords_matched,
    ARRAY_AGG(DISTINCT mc.concept_name) as concepts_used
FROM math_solutions ms
LEFT JOIN problem_classifications pc ON ms.solution_id = pc.solution_id
LEFT JOIN math_concepts_usage mc ON ms.solution_id = mc.solution_id
WHERE ms.agent_id = %s
    AND ms.complexity_level = 'advanced'
    AND ms.created_at >= %s
GROUP BY ms.solution_id, ms.problem, ms.problem_type, ms.complexity_level,
         ms.execution_time_ms, ms.confidence_score, pc.keywords_matched
ORDER BY ms.execution_time_ms DESC;

-- Get visualization effectiveness analysis
SELECT 
    problem_type,
    COUNT(*) as total_problems,
    SUM(CASE WHEN has_visualization THEN 1 ELSE 0 END) as with_visualizations,
    AVG(CASE WHEN has_visualization THEN confidence_score END) as avg_confidence_with_viz,
    AVG(CASE WHEN NOT has_visualization THEN confidence_score END) as avg_confidence_without_viz,
    AVG(CASE WHEN has_visualization THEN execution_time_ms END) as avg_time_with_viz
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= %s
GROUP BY problem_type
HAVING COUNT(*) >= 5
ORDER BY problem_type;

-- =====================================
-- Performance Monitoring Queries
-- =====================================

-- Check agent health metrics
SELECT 
    COUNT(*) as problems_last_hour,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(confidence_score) as avg_confidence,
    MAX(execution_time_ms) as max_execution_time,
    COUNT(CASE WHEN execution_time_ms > 30000 THEN 1 END) as slow_problems
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= NOW() - INTERVAL '1 hour';

-- Identify performance issues
SELECT 
    'high_execution_time' as issue_type,
    COUNT(*) as occurrence_count,
    AVG(execution_time_ms) as avg_time
FROM math_solutions
WHERE agent_id = %s
    AND execution_time_ms > 30000
    AND created_at >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'low_confidence' as issue_type,
    COUNT(*) as occurrence_count,
    AVG(confidence_score) as avg_confidence
FROM math_solutions
WHERE agent_id = %s
    AND confidence_score < 0.7
    AND created_at >= NOW() - INTERVAL '24 hours';

-- Get error patterns
SELECT 
    sv.issues_found,
    COUNT(*) as frequency,
    ARRAY_AGG(DISTINCT ms.problem_type) as affected_types
FROM solution_validations sv
JOIN math_solutions ms ON sv.solution_id = ms.solution_id
WHERE ms.agent_id = %s
    AND sv.is_correct = false
    AND sv.validation_timestamp >= %s
    AND array_length(sv.issues_found, 1) > 0
GROUP BY sv.issues_found
ORDER BY frequency DESC;

-- =====================================
-- Maintenance Queries
-- =====================================

-- Archive old solutions (older than 6 months)
DELETE FROM math_concepts_usage 
WHERE solution_id IN (
    SELECT solution_id FROM math_solutions 
    WHERE created_at < NOW() - INTERVAL '6 months'
);

DELETE FROM solution_validations 
WHERE solution_id IN (
    SELECT solution_id FROM math_solutions 
    WHERE created_at < NOW() - INTERVAL '6 months'
);

DELETE FROM problem_classifications 
WHERE solution_id IN (
    SELECT solution_id FROM math_solutions 
    WHERE created_at < NOW() - INTERVAL '6 months'
);

DELETE FROM math_solutions 
WHERE created_at < NOW() - INTERVAL '6 months';

-- Clean old metrics (older than 3 months)
DELETE FROM math_agent_metrics 
WHERE metric_date < CURRENT_DATE - INTERVAL '3 months';

-- Update table statistics
ANALYZE math_solutions;
ANALYZE problem_classifications;
ANALYZE solution_validations;
ANALYZE math_concepts_usage;
ANALYZE math_agent_metrics;

-- =====================================
-- Reporting Queries
-- =====================================

-- Daily performance report
SELECT 
    DATE(created_at) as solution_date,
    COUNT(*) as problems_solved,
    AVG(execution_time_ms) as avg_execution_time,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT problem_type) as problem_types,
    SUM(CASE WHEN has_visualization THEN 1 ELSE 0 END) as visualizations_created
FROM math_solutions
WHERE agent_id = %s
    AND created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY solution_date DESC;