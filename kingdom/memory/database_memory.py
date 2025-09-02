#!/usr/bin/env python3
"""
Database Memory System for Kingdom Agents

This module integrates the Kingdom agent system with the B2 Brain PostgreSQL database,
providing agents with persistent memory capabilities through the existing 19-entity schema.
"""

import json
import asyncio
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

from ..core.base_agent import BaseAgent, AgentMessage


class MemoryType(Enum):
    """Types of memories agents can store"""
    CONVERSATION = "conversation"      # Agent conversations and interactions
    TASK_EXECUTION = "task"           # Task execution records
    DECISION = "decision"             # Decision making processes
    LEARNING = "learning"             # Learned insights and patterns
    CONTEXT = "context"               # Contextual information
    RELATIONSHIP = "relationship"     # Inter-agent relationships
    KNOWLEDGE = "knowledge"           # Factual knowledge acquired
    EXPERIENCE = "experience"         # Experiential learning


@dataclass
class AgentMemory:
    """Structure for agent memory entries"""
    id: Optional[str]
    agent_id: str
    memory_type: MemoryType
    title: str
    content: Dict[str, Any]
    context_info: Dict[str, Any]
    tags: List[str]
    embedding_vector: Optional[List[float]] = None
    salience: float = 0.5  # Importance score 0-1
    emotion: Optional[str] = None
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    related_memories: List[str] = None


class DatabaseMemoryManager:
    """
    Manages agent memories using the B2 Brain PostgreSQL database.
    
    Maps agent memories to appropriate entity tables in the brain database,
    providing persistent storage and retrieval capabilities for all agents.
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection = None
        self.memory_table_mapping = {
            MemoryType.CONVERSATION: 'conversations',
            MemoryType.TASK_EXECUTION: 'tasks', 
            MemoryType.DECISION: 'events',  # Decisions are events
            MemoryType.LEARNING: 'knowledge_facts',
            MemoryType.CONTEXT: 'contexts',
            MemoryType.RELATIONSHIP: 'persons',  # Relationships with other agents/people
            MemoryType.KNOWLEDGE: 'knowledge_facts',
            MemoryType.EXPERIENCE: 'events'
        }
        
        # Cache for frequently accessed memories
        self.memory_cache: Dict[str, AgentMemory] = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cache_clean = datetime.now()
    
    async def connect(self):
        """Connect to the PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = True
            print(f"✅ Memory system connected to database: {self.db_config['database']}")
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            print("🔌 Memory system disconnected from database")
    
    async def store_memory(self, memory: AgentMemory) -> str:
        """Store a memory in the appropriate database table"""
        if not self.connection:
            await self.connect()
        
        table_name = self.memory_table_mapping.get(memory.memory_type, 'events')
        
        # Prepare data for insertion
        memory_data = self._prepare_memory_data(memory, table_name)
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Generate INSERT query
            columns = list(memory_data.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                RETURNING id
            """
            
            cursor.execute(query, list(memory_data.values()))
            memory_id = cursor.fetchone()[0]
            
            memory.id = memory_id
            
            # Cache the memory
            self.memory_cache[memory_id] = memory
            
            cursor.close()
            print(f"💾 Stored {memory.memory_type.value} memory: {memory.title}")
            return memory_id
            
        except psycopg2.Error as e:
            print(f"❌ Error storing memory: {e}")
            raise
    
    async def retrieve_memory(self, memory_id: str) -> Optional[AgentMemory]:
        """Retrieve a specific memory by ID"""
        # Check cache first
        if memory_id in self.memory_cache:
            return self.memory_cache[memory_id]
        
        if not self.connection:
            await self.connect()
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Search across all possible tables
            for memory_type, table_name in self.memory_table_mapping.items():
                query = f"SELECT * FROM {table_name} WHERE id = %s"
                cursor.execute(query, (memory_id,))
                result = cursor.fetchone()
                
                if result:
                    memory = self._parse_memory_from_row(dict(result), memory_type)
                    self.memory_cache[memory_id] = memory
                    cursor.close()
                    return memory
            
            cursor.close()
            return None
            
        except psycopg2.Error as e:
            print(f"❌ Error retrieving memory: {e}")
            return None
    
    async def search_memories(self, agent_id: str, 
                            memory_type: MemoryType = None,
                            tags: List[str] = None,
                            text_query: str = None,
                            limit: int = 50) -> List[AgentMemory]:
        """Search memories for a specific agent"""
        if not self.connection:
            await self.connect()
        
        memories = []
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Determine which tables to search
            tables_to_search = []
            if memory_type:
                tables_to_search.append((memory_type, self.memory_table_mapping[memory_type]))
            else:
                tables_to_search = list(self.memory_table_mapping.items())
            
            for mem_type, table_name in tables_to_search:
                # Build search query
                conditions = ["source_info->>'agent_id' = %s"]
                params = [agent_id]
                
                # Tag filtering
                if tags:
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append("tags ? %s")
                        params.append(tag)
                    conditions.append(f"({' OR '.join(tag_conditions)})")
                
                # Text search
                if text_query:
                    conditions.append("(title ILIKE %s OR summary ILIKE %s OR description ILIKE %s)")
                    search_pattern = f"%{text_query}%"
                    params.extend([search_pattern, search_pattern, search_pattern])
                
                query = f"""
                    SELECT * FROM {table_name}
                    WHERE {' AND '.join(conditions)}
                    ORDER BY updated_at DESC
                    LIMIT %s
                """
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                for row in results:
                    memory = self._parse_memory_from_row(dict(row), mem_type)
                    memories.append(memory)
            
            cursor.close()
            
            # Sort by updated_at and limit
            memories.sort(key=lambda x: x.updated_at or datetime.min, reverse=True)
            return memories[:limit]
            
        except psycopg2.Error as e:
            print(f"❌ Error searching memories: {e}")
            return []
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory"""
        if not self.connection:
            await self.connect()
        
        # Remove from cache to force reload
        if memory_id in self.memory_cache:
            del self.memory_cache[memory_id]
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Find the table containing this memory
            for memory_type, table_name in self.memory_table_mapping.items():
                # Check if memory exists in this table
                check_query = f"SELECT id FROM {table_name} WHERE id = %s"
                cursor.execute(check_query, (memory_id,))
                
                if cursor.fetchone():
                    # Build update query
                    set_clauses = []
                    params = []
                    
                    for key, value in updates.items():
                        if key in ['content', 'context_info', 'source_info', 'metadata']:
                            # JSON fields
                            set_clauses.append(f"{key} = %s::jsonb")
                        elif key in ['tags']:
                            # Array fields
                            set_clauses.append(f"{key} = %s")
                        else:
                            set_clauses.append(f"{key} = %s")
                        params.append(value)
                    
                    set_clauses.append("updated_at = %s")
                    params.append(datetime.now())
                    
                    params.append(memory_id)  # for WHERE clause
                    
                    update_query = f"""
                        UPDATE {table_name}
                        SET {', '.join(set_clauses)}
                        WHERE id = %s
                    """
                    
                    cursor.execute(update_query, params)
                    cursor.close()
                    return True
            
            cursor.close()
            return False
            
        except psycopg2.Error as e:
            print(f"❌ Error updating memory: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from the database"""
        if not self.connection:
            await self.connect()
        
        # Remove from cache
        if memory_id in self.memory_cache:
            del self.memory_cache[memory_id]
        
        try:
            cursor = self.connection.cursor()
            
            # Find and delete from the appropriate table
            for table_name in self.memory_table_mapping.values():
                query = f"DELETE FROM {table_name} WHERE id = %s"
                cursor.execute(query, (memory_id,))
                
                if cursor.rowcount > 0:
                    cursor.close()
                    print(f"🗑️  Deleted memory: {memory_id}")
                    return True
            
            cursor.close()
            return False
            
        except psycopg2.Error as e:
            print(f"❌ Error deleting memory: {e}")
            return False
    
    async def get_agent_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get memory statistics for an agent"""
        if not self.connection:
            await self.connect()
        
        stats = {
            'total_memories': 0,
            'by_type': {},
            'recent_activity': 0,  # memories in last 24h
            'most_common_tags': []
        }
        
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for memory_type, table_name in self.memory_table_mapping.items():
                # Count memories by type
                count_query = f"""
                    SELECT COUNT(*) as count,
                           COUNT(CASE WHEN created_at >= %s THEN 1 END) as recent_count
                    FROM {table_name}
                    WHERE source_info->>'agent_id' = %s
                """
                cursor.execute(count_query, (yesterday, agent_id))
                result = cursor.fetchone()
                
                count = result['count']
                recent_count = result['recent_count']
                
                if count > 0:
                    stats['by_type'][memory_type.value] = count
                    stats['total_memories'] += count
                    stats['recent_activity'] += recent_count
            
            cursor.close()
            return stats
            
        except psycopg2.Error as e:
            print(f"❌ Error getting memory stats: {e}")
            return stats
    
    def _prepare_memory_data(self, memory: AgentMemory, table_name: str) -> Dict[str, Any]:
        """Prepare memory data for database insertion"""
        now = datetime.now()
        
        # Base data that all tables have (from the core convention)
        base_data = {
            'type': memory.memory_type.value,
            'title': memory.title,
            'summary': memory.title,  # Use title as summary for now
            'description': json.dumps(memory.content) if memory.content else None,
            'tags': memory.tags,
            'salience': memory.salience,
            'emotion': memory.emotion,
            'confidence': memory.confidence,
            'created_at': now,
            'updated_at': now,
            'source_info': json.dumps({
                'agent_id': memory.agent_id,
                'system': 'kingdom_agents'
            }),
            'metadata': json.dumps(memory.context_info or {}),
            'privacy_info': json.dumps({'level': 'agent_private'}),
            'access_info': json.dumps({'owner': memory.agent_id})
        }
        
        # Add embedding if available
        if memory.embedding_vector:
            base_data['embedding_refs'] = json.dumps({
                'vector': memory.embedding_vector,
                'model': 'openai_embedding',
                'created_at': now.isoformat()
            })
        
        # Add links to related memories
        if memory.related_memories:
            base_data['links'] = json.dumps({
                'related_memories': memory.related_memories
            })
        
        return base_data
    
    def _parse_memory_from_row(self, row: Dict[str, Any], memory_type: MemoryType) -> AgentMemory:
        """Parse database row into AgentMemory object"""
        # Extract agent ID from source_info
        source_info = row.get('source_info') or {}
        if isinstance(source_info, str):
            source_info = json.loads(source_info)
        
        agent_id = source_info.get('agent_id', 'unknown')
        
        # Parse content from description
        content = {}
        if row.get('description'):
            try:
                content = json.loads(row['description'])
            except (json.JSONDecodeError, TypeError):
                content = {'raw': row['description']}
        
        # Parse context from metadata
        context_info = row.get('metadata') or {}
        if isinstance(context_info, str):
            try:
                context_info = json.loads(context_info)
            except (json.JSONDecodeError, TypeError):
                context_info = {}
        
        # Parse related memories from links
        related_memories = []
        links = row.get('links') or {}
        if isinstance(links, str):
            try:
                links = json.loads(links)
                related_memories = links.get('related_memories', [])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Parse embedding
        embedding_vector = None
        embedding_refs = row.get('embedding_refs')
        if embedding_refs:
            if isinstance(embedding_refs, str):
                try:
                    embedding_data = json.loads(embedding_refs)
                    embedding_vector = embedding_data.get('vector')
                except (json.JSONDecodeError, TypeError):
                    pass
        
        return AgentMemory(
            id=str(row['id']),
            agent_id=agent_id,
            memory_type=memory_type,
            title=row.get('title', ''),
            content=content,
            context_info=context_info,
            tags=row.get('tags', []),
            embedding_vector=embedding_vector,
            salience=float(row.get('salience', 0.5)),
            emotion=row.get('emotion'),
            confidence=float(row.get('confidence', 1.0)),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            related_memories=related_memories
        )
    
    async def cleanup_cache(self):
        """Clean up expired cache entries"""
        now = datetime.now()
        if (now - self.last_cache_clean).seconds > self.cache_ttl:
            # In a real implementation, you'd track cache timestamps
            # For now, just clear the cache periodically
            if len(self.memory_cache) > 1000:  # Arbitrary limit
                self.memory_cache.clear()
            self.last_cache_clean = now


class AgentMemoryInterface:
    """
    Interface for agents to interact with their memory system.
    This class is injected into agents to provide memory capabilities.
    """
    
    def __init__(self, agent_id: str, memory_manager: DatabaseMemoryManager):
        self.agent_id = agent_id
        self.memory_manager = memory_manager
    
    async def remember(self, memory_type: MemoryType, title: str, 
                      content: Dict[str, Any], 
                      context: Dict[str, Any] = None,
                      tags: List[str] = None,
                      salience: float = 0.5,
                      emotion: str = None) -> str:
        """Store a new memory"""
        memory = AgentMemory(
            id=None,
            agent_id=self.agent_id,
            memory_type=memory_type,
            title=title,
            content=content,
            context_info=context or {},
            tags=tags or [],
            salience=salience,
            emotion=emotion
        )
        
        return await self.memory_manager.store_memory(memory)
    
    async def recall(self, memory_id: str) -> Optional[AgentMemory]:
        """Retrieve a specific memory"""
        return await self.memory_manager.retrieve_memory(memory_id)
    
    async def search(self, query: str = None, 
                    memory_type: MemoryType = None,
                    tags: List[str] = None,
                    limit: int = 20) -> List[AgentMemory]:
        """Search memories"""
        return await self.memory_manager.search_memories(
            self.agent_id, memory_type, tags, query, limit
        )
    
    async def get_recent_memories(self, limit: int = 10) -> List[AgentMemory]:
        """Get most recent memories"""
        return await self.search(limit=limit)
    
    async def get_memories_by_type(self, memory_type: MemoryType, limit: int = 20) -> List[AgentMemory]:
        """Get memories of a specific type"""
        return await self.search(memory_type=memory_type, limit=limit)
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing memory"""
        return await self.memory_manager.update_memory(memory_id, updates)
    
    async def forget(self, memory_id: str) -> bool:
        """Delete a memory"""
        return await self.memory_manager.delete_memory(memory_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics for this agent"""
        return await self.memory_manager.get_agent_memory_stats(self.agent_id)


# Helper functions for common memory operations

async def create_conversation_memory(memory_interface: AgentMemoryInterface,
                                   conversation_id: str, 
                                   participants: List[str],
                                   messages: List[AgentMessage],
                                   summary: str = None) -> str:
    """Helper to create a conversation memory"""
    content = {
        'conversation_id': conversation_id,
        'participants': participants,
        'message_count': len(messages),
        'messages': [msg.to_dict() for msg in messages[-10:]],  # Store last 10 messages
        'summary': summary or f"Conversation between {', '.join(participants)}"
    }
    
    return await memory_interface.remember(
        memory_type=MemoryType.CONVERSATION,
        title=f"Conversation: {conversation_id[:8]}",
        content=content,
        tags=['conversation', 'communication'] + participants
    )

async def create_task_memory(memory_interface: AgentMemoryInterface,
                           task_id: str, task_data: Dict[str, Any],
                           result: Any, execution_time: float) -> str:
    """Helper to create a task execution memory"""
    content = {
        'task_id': task_id,
        'task_data': task_data,
        'result': result,
        'execution_time_seconds': execution_time,
        'status': 'completed'
    }
    
    return await memory_interface.remember(
        memory_type=MemoryType.TASK_EXECUTION,
        title=f"Task: {task_data.get('name', task_id)}",
        content=content,
        tags=['task', 'execution', 'completed']
    )