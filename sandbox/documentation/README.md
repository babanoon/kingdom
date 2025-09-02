# GeneralReceiver Agent

## Overview

The **GeneralReceiver Agent** is the primary entry point for the Kingdom Agent System, designed to handle general questions, conversations, and intelligently route specialized requests to appropriate expert agents. This agent serves as the "front desk" of the Kingdom system, providing helpful responses while maintaining context and routing complex queries to specialists.

## Agent Architecture

### 🧠 Brain (GenAI Model)
- **Primary**: Google Gemini for natural language processing
- **Capabilities**: General reasoning, conversation management, intent recognition
- **Thinking Modes**: Conversational, Analytical, Creative

### ✋ Hands (Code Execution)
- Text processing and response formatting
- Message routing logic and decision making
- Database logging and analytics queries
- A2A message handling and dispatch

### 👂 Ears (Input Listening)
- Management API endpoints (`/api/chat`)
- Rocket.Chat integration (webhook support)
- A2A message bus for inter-agent communication
- WebSocket connections for real-time updates

### 👅 Tongue (Communication)
- Structured JSON responses for API clients
- Markdown-formatted responses for documentation
- A2A messages to specialist agents
- Real-time WebSocket notifications

### 👀 Eyes (Self-Assessment)
- Conversation quality monitoring
- Response time tracking
- Routing accuracy assessment
- Performance metrics collection

### 🦵 Legs (Environment)
- Lightweight deployment footprint
- Fast response times for user interactions
- Scalable for high conversation volumes
- Integration with Kingdom service infrastructure

### 🦷 Teeth (Security)
- Input sanitization and validation
- Content safety filtering
- Rate limiting and abuse prevention
- Secure credential handling

## Key Features

### 1. **Intelligent Conversation Handling**
- Maintains conversation context across multiple interactions
- Provides helpful, contextually appropriate responses
- Handles follow-up questions and clarifications
- Supports multiple conversation formats (chat, Q&A, structured queries)

### 2. **Smart Message Routing**
- Automatically detects when questions require specialist knowledge
- Routes mathematical queries to MathCalculator agent
- Forwards database questions to Tester agents
- Delegates strategic planning to Vazir agent
- Provides transparent routing explanations to users

### 3. **Multi-Platform Integration**
- RESTful API endpoints for external systems
- Webhook support for Rocket.Chat and other platforms
- Real-time WebSocket connections for live updates
- A2A messaging with other Kingdom agents

### 4. **Comprehensive Logging & Analytics**
- Detailed conversation logging with performance metrics
- Routing decision tracking and analysis
- Agent performance monitoring and alerting
- Historical analytics for system optimization

## File Structure

```
general_receiver/
├── agent.py          # Main agent implementation
├── prompts.txt       # AI prompts and personality guidelines  
├── schema.json       # JSON schemas for inputs/outputs
├── config.json       # Agent configuration and settings
├── queries.sql       # Database queries for logging/analytics
└── README.md         # This documentation file
```

## Configuration

### Runtime Settings (`config.json`)
- **Conversation History**: Maintains last 10 interactions by default
- **Response Timeout**: 30 seconds maximum for AI responses
- **Routing Enabled**: Automatic routing to specialist agents
- **Safety Level**: Medium content filtering
- **Gemini Model**: Uses gemini-pro for AI responses

### Routing Rules
The agent uses keyword-based routing with confidence thresholds:
- **Mathematical**: Keywords like "calculate", "solve", "equation" → MathCalculator
- **Database**: Keywords like "sql", "query", "database" → Tester agents  
- **Testing**: Keywords like "test", "validate", "verify" → Testing agents
- **Strategic**: Keywords like "plan", "strategy", "decision" → Vazir agent

## API Endpoints

### Main Chat Endpoint
```http
POST /api/chat
Content-Type: application/json

{
  "sender": "user123",
  "receiver": "general_receiver",
  "forum": "support_channel", 
  "message": "What is the capital of France?"
}
```

### Response Format
```json
{
  "success": true,
  "response": "The capital of France is Paris...",
  "agent_id": "general_receiver_001",
  "processing_time_ms": 1200,
  "workflow_id": "workflow_20250901_123456_abc123",
  "routed": false
}
```

## Usage Examples

### 1. General Question
**Input**: "What is machine learning?"
**Response**: Provides comprehensive explanation of ML concepts, applications, and key algorithms.

### 2. Mathematical Routing
**Input**: "Can you calculate 15% compound interest on $5000 over 3 years?"
**Response**: "I'll connect you with our mathematical specialist who can provide precise calculations with step-by-step solutions."
**Action**: Routes to MathCalculator agent

### 3. Context Maintenance
**Input**: "What about its history?"
**Response**: (Referring to previous Paris discussion) "Paris has a rich history spanning over 2,000 years..."

### 4. Database Query Routing
**Input**: "How do I create a SQL table with foreign keys?"
**Response**: "I'll route your database question to our SQL specialist who can provide detailed schema examples."
**Action**: Routes to appropriate Tester agent

## Integration Points

### Kingdom Service Integration
- Inherits from `ServiceAgent` base class
- Integrates with Kingdom task queue system
- Uses existing A2A message bus infrastructure
- Leverages Kingdom logging and monitoring systems

### Database Integration
- Uses existing PostgreSQL connection pooling
- Stores conversations in `conversation_logs` table
- Tracks routing decisions in `routing_decisions` table
- Collects performance metrics in `agent_metrics` table

### External Platform Integration
- **Rocket.Chat**: Webhook endpoints for message processing
- **Management API**: RESTful endpoints for external systems
- **WebSocket**: Real-time monitoring and notifications
- **Other Platforms**: Extensible webhook architecture

## Monitoring & Analytics

### Performance Metrics
- Average response time per conversation
- Routing accuracy and frequency
- Conversation volume trends
- Error rates and issue tracking

### Health Monitoring
- Real-time health check endpoints
- Performance threshold alerting
- Memory and CPU usage tracking
- Database connection monitoring

### Analytics Queries
The `queries.sql` file provides comprehensive analytics:
- Conversation history and trends
- Routing effectiveness analysis
- Performance optimization insights
- User interaction patterns

## Development & Testing

### Testing the Agent
```bash
# Start Kingdom Management Server
python kingdom/management/management_server.py

# Test via curl
curl -X POST http://localhost:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "Hello, can you help me with a math problem?"
  }'
```

### A2A Communication Testing
```python
# Test A2A messaging between agents
await general_receiver.send_a2a_message("math_calculator_001", {
    "type": "routed_request",
    "payload": {"message": "Calculate 2+2"},
    "return_address": "general_receiver_001"
})
```

### Performance Testing
```bash
# Monitor agent performance
curl http://localhost:8765/api/agents
curl http://localhost:8765/api/workflows
```

## Deployment Considerations

### Scaling
- Designed for high concurrent conversation loads
- Stateless design allows horizontal scaling  
- Conversation history stored in database, not memory
- Efficient routing algorithms minimize processing overhead

### Security
- Input validation and sanitization
- Content safety filtering
- Rate limiting to prevent abuse
- Secure credential management

### Monitoring
- Comprehensive logging for debugging
- Performance metrics for optimization
- Alert thresholds for proactive monitoring
- Health check endpoints for load balancers

## Future Enhancements

### Planned Features
- **Context Learning**: Improve responses based on conversation patterns
- **User Personalization**: Adapt responses to individual user preferences
- **Advanced Routing**: ML-based routing decisions instead of keyword matching
- **Multi-language Support**: Handle conversations in multiple languages

### Integration Opportunities
- **Voice Interface**: Speech-to-text and text-to-speech capabilities
- **Rich Media**: Support for images, documents, and interactive content
- **External APIs**: Integration with search engines, knowledge bases
- **Workflow Automation**: Trigger complex multi-agent workflows

## Support

For questions about the GeneralReceiver agent:
1. Check the configuration in `config.json`
2. Review conversation logs in the database
3. Monitor performance metrics via API endpoints
4. Test A2A communication with other agents
5. Verify Kingdom service integration

The GeneralReceiver agent is the foundation of user interaction with the Kingdom system - reliable, intelligent, and extensible for future enhancements.