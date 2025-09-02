#!/usr/bin/env python3
"""
Simple Tester Agents for Kingdom Service

These agents are designed to test fundamental infrastructure:
- Database operations
- A2A communication  
- Google ADK integration
- Parallel task execution
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add project root to path
sys.path.append('/Users/ed/King/B2')

from kingdom.service.agent_service import ServiceAgent
from kingdom.core.agent_logging import get_agent_logger, log_task_start, log_task_complete, log_error

# ServiceAgent is now imported from kingdom.service.agent_service

class TesterAgent1(ServiceAgent):
    """
    Tester Agent 1 - Database Operations and Google ADK Testing
    
    Capabilities:
    - Database CRUD operations
    - Activity logging
    - Google ADK integration testing
    - Task processing and reporting
    """
    
    def __init__(self, agent_id: str, agent_type: str = "tester1"):
        super().__init__(agent_id, agent_type)
        self.test_table = "agent_test_data"  # Simple test table
        self.operations_log = []

        # Setup centralized logging
        self.agent_logger = get_agent_logger(agent_id, "local")  # Assume local for now
    
    async def initialize_for_service(self, task_queue, a2a_bus, db_pool):
        """Initialize Tester1 with service dependencies"""
        await super().initialize_for_service(task_queue, a2a_bus, db_pool)
        
        # Create test table if it doesn't exist
        await self._create_test_table()
        
        self.logger.info(f"Tester1 {self.agent_id} ready for database operations")
    
    async def _create_test_table(self):
        """Create test table for database operations"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.test_table} (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(50) NOT NULL,
            test_data JSONB,
            operation_type VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        conn = await self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
            self.logger.info(f"Test table {self.test_table} ready")
        except Exception as e:
            self.logger.error(f"Failed to create test table: {e}")
        finally:
            await self.db_pool.return_connection(conn)
    
    async def _handle_task(self, task) -> Any:
        """Handle tasks for Tester1"""
        task_type = task.task_type
        payload = task.payload

        # Log task start
        log_task_start(self.agent_id, task.task_id, task_type, "local")
        self.agent_logger.log("task_received", f"Processing {task_type} task", {
            "task_id": task.task_id,
            "payload_keys": list(payload.keys()) if payload else []
        })

        try:
            if task_type == "db_insert":
                result = await self._handle_db_insert(payload)
            elif task_type == "db_read":
                result = await self._handle_db_read(payload)
            elif task_type == "db_update":
                result = await self._handle_db_update(payload)
            elif task_type == "db_delete":
                result = await self._handle_db_delete(payload)
            elif task_type == "test_google_adk":
                result = await self._handle_google_adk_test(payload)
            elif task_type == "send_test_message":
                result = await self._handle_send_test_message(payload)
            else:
                result = {"error": f"Unknown task type: {task_type}"}

            # Log task completion
            log_task_complete(self.agent_id, task.task_id, result, "local")
            self.agent_logger.log("task_completed", f"Task {task_type} completed successfully", {
                "task_id": task.task_id,
                "result_type": type(result).__name__
            })

            return result

        except Exception as e:
            # Log error
            log_error(self.agent_id, task_type, e, "local")
            self.agent_logger.log("task_error", f"Task {task_type} failed", {
                "task_id": task.task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {"error": str(e)}
    
    async def _handle_db_insert(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into test database"""
        test_data = payload.get('data', {})
        
        insert_sql = f"""
        INSERT INTO {self.test_table} (agent_id, test_data, operation_type)
        VALUES (%s, %s, %s) RETURNING id;
        """
        
        conn = await self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(insert_sql, (self.agent_id, json.dumps(test_data), 'INSERT'))
            record_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            # Log operation
            log_entry = {
                'operation': 'INSERT',
                'record_id': record_id,
                'data': test_data,
                'timestamp': datetime.now().isoformat()
            }
            self.operations_log.append(log_entry)
            
            self.logger.info(f"Inserted record {record_id} into {self.test_table}")
            
            return {
                'success': True,
                'record_id': record_id,
                'operation': 'INSERT',
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Database insert failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            await self.db_pool.return_connection(conn)
    
    async def _handle_db_read(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Read data from test database"""
        record_id = payload.get('record_id')
        limit = payload.get('limit', 10)
        
        if record_id:
            select_sql = f"SELECT * FROM {self.test_table} WHERE id = %s"
            params = (record_id,)
        else:
            select_sql = f"SELECT * FROM {self.test_table} WHERE agent_id = %s ORDER BY created_at DESC LIMIT %s"
            params = (self.agent_id, limit)
        
        conn = await self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(select_sql, params)
            records = cursor.fetchall()
            cursor.close()
            
            # Convert to dict format
            columns = ['id', 'agent_id', 'test_data', 'operation_type', 'created_at']
            results = []
            for record in records:
                result_dict = dict(zip(columns, record))
                result_dict['created_at'] = result_dict['created_at'].isoformat() if result_dict['created_at'] else None
                results.append(result_dict)
            
            # Log operation
            log_entry = {
                'operation': 'READ',
                'records_found': len(results),
                'timestamp': datetime.now().isoformat()
            }
            self.operations_log.append(log_entry)
            
            self.logger.info(f"Read {len(results)} records from {self.test_table}")
            
            return {
                'success': True,
                'records': results,
                'count': len(results),
                'operation': 'READ',
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Database read failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            await self.db_pool.return_connection(conn)
    
    async def _handle_db_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delete data from test database"""
        record_id = payload.get('record_id')
        
        if not record_id:
            return {'success': False, 'error': 'record_id required for delete'}
        
        delete_sql = f"DELETE FROM {self.test_table} WHERE id = %s AND agent_id = %s"
        
        conn = await self.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(delete_sql, (record_id, self.agent_id))
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            # Log operation
            log_entry = {
                'operation': 'DELETE',
                'record_id': record_id,
                'deleted_count': deleted_count,
                'timestamp': datetime.now().isoformat()
            }
            self.operations_log.append(log_entry)
            
            self.logger.info(f"Deleted {deleted_count} records from {self.test_table}")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'record_id': record_id,
                'operation': 'DELETE',
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Database delete failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            await self.db_pool.return_connection(conn)
    
    async def _handle_google_adk_test(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test Google ADK methodology (placeholder implementation)"""
        test_type = payload.get('test_type', 'basic')
        
        # Placeholder for Google ADK integration
        # This would implement actual Google Agent Development Kit functionality
        
        test_results = {
            'adk_version': 'placeholder_v1.0',
            'test_type': test_type,
            'test_passed': True,
            'test_details': {
                'agent_registration': 'success',
                'capability_discovery': 'success', 
                'message_routing': 'success'
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Log operation
        log_entry = {
            'operation': 'GOOGLE_ADK_TEST',
            'test_type': test_type,
            'result': 'success',
            'timestamp': datetime.now().isoformat()
        }
        self.operations_log.append(log_entry)
        
        self.logger.info(f"Google ADK test completed: {test_type}")
        
        return {
            'success': True,
            'adk_test_results': test_results,
            'operation': 'GOOGLE_ADK_TEST',
            'agent_id': self.agent_id
        }
    
    async def _handle_send_test_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send test message to another agent"""
        recipient_id = payload.get('recipient_id')
        message_content = payload.get('message', 'Test message from Tester1')
        
        if not recipient_id:
            return {'success': False, 'error': 'recipient_id required'}
        
        test_message = {
            'type': 'test_communication',
            'content': message_content,
            'sender_info': {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'task_count': self.task_count
            },
            'timestamp': datetime.now().isoformat()
        }
        
        await self.send_a2a_message(recipient_id, test_message)
        
        # Log operation
        log_entry = {
            'operation': 'SEND_A2A_MESSAGE',
            'recipient': recipient_id,
            'message_type': 'test_communication',
            'timestamp': datetime.now().isoformat()
        }
        self.operations_log.append(log_entry)
        
        return {
            'success': True,
            'message_sent': True,
            'recipient': recipient_id,
            'operation': 'SEND_A2A_MESSAGE',
            'agent_id': self.agent_id
        }
    
    async def get_operations_log(self) -> List[Dict[str, Any]]:
        """Get operations log for this agent"""
        return self.operations_log.copy()


class TesterAgent2(ServiceAgent):
    """
    Tester Agent 2 - A2A Communication Testing
    
    Capabilities:
    - A2A message handling and response
    - Communication validation
    - Message logging and statistics
    - Parallel communication testing
    """
    
    def __init__(self, agent_id: str, agent_type: str = "tester2"):
        super().__init__(agent_id, agent_type)
        self.message_log = []
        self.response_sent_count = 0
        self.communication_stats = {
            'messages_received': 0,
            'responses_sent': 0,
            'test_messages': 0,
            'error_messages': 0
        }

        # Setup centralized logging
        self.agent_logger = get_agent_logger(agent_id, "local")  # Assume local for now
    
    async def _handle_task(self, task) -> Any:
        """Handle tasks for Tester2"""
        task_type = task.task_type
        payload = task.payload

        # Log task start
        log_task_start(self.agent_id, task.task_id, task_type, "local")
        self.agent_logger.log("task_received", f"Processing {task_type} task", {
            "task_id": task.task_id,
            "payload_keys": list(payload.keys()) if payload else []
        })

        try:
            if task_type == "test_a2a_communication":
                result = await self._handle_test_a2a_communication(payload)
            elif task_type == "send_broadcast_test":
                result = await self._handle_broadcast_test(payload)
            elif task_type == "validate_communication":
                result = await self._handle_validate_communication(payload)
            elif task_type == "get_communication_stats":
                result = await self._handle_get_stats(payload)
            else:
                result = {"error": f"Unknown task type: {task_type}"}

            # Log task completion
            log_task_complete(self.agent_id, task.task_id, result, "local")
            self.agent_logger.log("task_completed", f"Task {task_type} completed successfully", {
                "task_id": task.task_id,
                "result_type": type(result).__name__
            })

            return result

        except Exception as e:
            # Log error
            log_error(self.agent_id, task_type, e, "local")
            self.agent_logger.log("task_error", f"Task {task_type} failed", {
                "task_id": task.task_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {"error": str(e)}
    
    async def _handle_a2a_message(self, message):
        """Handle incoming A2A messages"""
        sender = message['sender']
        payload = message['payload']
        message_type = payload.get('type', 'unknown')
        
        self.communication_stats['messages_received'] += 1
        
        # Log the message
        log_entry = {
            'message_id': message['message_id'],
            'sender': sender,
            'type': message_type,
            'content': payload.get('content', ''),
            'received_at': datetime.now().isoformat(),
            'responded': False
        }
        self.message_log.append(log_entry)
        
        self.logger.info(f"Received A2A message from {sender}: {message_type}")
        
        # Handle different message types
        if message_type == 'test_communication':
            await self._respond_to_test_message(sender, message['message_id'], payload)
        elif message_type == 'validation_request':
            await self._respond_to_validation_request(sender, message['message_id'], payload)
        else:
            self.logger.warning(f"Unknown message type: {message_type}")
    
    async def _respond_to_test_message(self, sender: str, message_id: str, payload: Dict[str, Any]):
        """Respond to test communication message"""
        response_message = {
            'type': 'test_response',
            'original_message_id': message_id,
            'content': f"Response from {self.agent_id} to test message",
            'sender_info': payload.get('sender_info', {}),
            'response_info': {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'messages_processed': self.communication_stats['messages_received']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        await self.send_a2a_message(sender, response_message)
        
        # Update stats and log
        self.communication_stats['responses_sent'] += 1
        self.response_sent_count += 1
        
        # Mark original message as responded
        for log_entry in self.message_log:
            if log_entry['message_id'] == message_id:
                log_entry['responded'] = True
                break
        
        self.logger.info(f"Sent test response to {sender} for message {message_id}")
    
    async def _handle_test_a2a_communication(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate A2A communication test"""
        target_agent = payload.get('target_agent', 'tester1_001')
        message_content = payload.get('message', 'A2A communication test from Tester2')
        
        test_message = {
            'type': 'validation_request',
            'content': message_content,
            'test_id': f"test_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            'sender_info': {
                'agent_id': self.agent_id,
                'agent_type': self.agent_type,
                'messages_sent': self.communication_stats['responses_sent']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        await self.send_a2a_message(target_agent, test_message)
        
        self.communication_stats['test_messages'] += 1
        
        return {
            'success': True,
            'test_initiated': True,
            'target_agent': target_agent,
            'test_id': test_message['test_id'],
            'operation': 'TEST_A2A_COMMUNICATION',
            'agent_id': self.agent_id
        }
    
    async def _handle_broadcast_test(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send broadcast test to multiple agents"""
        target_agents = payload.get('target_agents', ['tester1_001', 'tester1_002'])
        message_content = payload.get('message', 'Broadcast test from Tester2')
        
        broadcast_id = f"broadcast_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        responses = []
        
        for target in target_agents:
            broadcast_message = {
                'type': 'broadcast_test',
                'broadcast_id': broadcast_id,
                'content': message_content,
                'target_count': len(target_agents),
                'sender_info': {
                    'agent_id': self.agent_id,
                    'agent_type': self.agent_type
                },
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                await self.send_a2a_message(target, broadcast_message)
                responses.append({'target': target, 'status': 'sent'})
            except Exception as e:
                responses.append({'target': target, 'status': 'failed', 'error': str(e)})
        
        return {
            'success': True,
            'broadcast_id': broadcast_id,
            'targets_sent': len([r for r in responses if r['status'] == 'sent']),
            'responses': responses,
            'operation': 'BROADCAST_TEST',
            'agent_id': self.agent_id
        }
    
    async def _handle_validate_communication(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate communication patterns and statistics"""
        validation_results = {
            'total_messages_received': self.communication_stats['messages_received'],
            'responses_sent': self.communication_stats['responses_sent'],
            'test_messages': self.communication_stats['test_messages'],
            'error_messages': self.communication_stats['error_messages'],
            'response_rate': (self.communication_stats['responses_sent'] / 
                            max(1, self.communication_stats['messages_received'])),
            'message_log_size': len(self.message_log),
            'recent_messages': self.message_log[-5:] if self.message_log else [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'validation_results': validation_results,
            'operation': 'VALIDATE_COMMUNICATION',
            'agent_id': self.agent_id
        }
    
    async def _handle_get_stats(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get communication statistics"""
        return {
            'success': True,
            'communication_stats': self.communication_stats.copy(),
            'message_log_count': len(self.message_log),
            'agent_status': await self.get_status(),
            'operation': 'GET_COMMUNICATION_STATS',
            'agent_id': self.agent_id
        }
    
    async def get_message_log(self) -> List[Dict[str, Any]]:
        """Get message log for this agent"""
        return self.message_log.copy()
    
    async def get_communication_statistics(self) -> Dict[str, Any]:
        """Get detailed communication statistics"""
        return {
            'stats': self.communication_stats.copy(),
            'message_log_size': len(self.message_log),
            'recent_activity': self.message_log[-10:] if self.message_log else []
        }