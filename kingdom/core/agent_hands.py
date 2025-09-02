#!/usr/bin/env python3
"""
Agent Hands - Code Execution System

This module provides the "hands" functionality for agents, allowing them to
execute Python code, SQL queries, bash commands, and interact with APIs
to perform actual tasks and computations.
"""

import os
import subprocess
import tempfile
import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class ExecutionEnvironment(Enum):
    """Execution environments for different types of code"""
    PYTHON = "python"
    BASH = "bash"
    SQL = "sql"
    API = "api"
    FILE_SYSTEM = "filesystem"

class ExecutionResult(Enum):
    """Execution result types"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"

@dataclass
class ExecutionContext:
    """Context for code execution"""
    environment: ExecutionEnvironment
    code: str
    parameters: Dict[str, Any]
    working_directory: str
    timeout_seconds: int = 30
    allowed_imports: List[str] = None
    environment_variables: Dict[str, str] = None

@dataclass
class ExecutionOutput:
    """Result of code execution"""
    execution_id: str
    context: ExecutionContext
    result: ExecutionResult
    output: str
    error_message: Optional[str]
    return_value: Any
    execution_time: float
    timestamp: datetime
    resources_used: Dict[str, Any]

class AgentHands:
    """
    The "hands" of an agent - handles all code execution and task performance.
    
    This class allows agents to actually DO things through code execution,
    database queries, API calls, and system interactions.
    """
    
    def __init__(self, agent_id: str, working_directory: str = None):
        self.agent_id = agent_id
        self.working_directory = working_directory or f"./kingdom/agents/{agent_id}/workspace"
        
        # Execution history
        self.execution_history: List[ExecutionOutput] = []
        
        # Security and resource limits
        self.max_execution_time = 300  # 5 minutes
        self.max_memory_mb = 1024
        self.allowed_packages = {
            'pandas', 'numpy', 'json', 'requests', 'datetime', 'os', 'sys',
            'pathlib', 'csv', 'sqlite3', 'psycopg2', 'asyncio', 'aiohttp',
            'matplotlib', 'seaborn', 'scipy', 'sklearn', 'openai'
        }
        
        # Database connections
        self.db_connections = {}
        self._initialize_db_connections()
        
        # Ensure working directory exists
        os.makedirs(self.working_directory, exist_ok=True)
        
        print(f"✋ Agent Hands initialized for {agent_id} - workspace: {self.working_directory}")
    
    def _initialize_db_connections(self):
        """Initialize database connections"""
        try:
            # PostgreSQL connection for B2 database
            db_config = {
                "host": "localhost",
                "port": 9876,
                "database": "general2613",
                "user": "kadmin",
                "password": "securepasswordkossher123"
            }
            self.db_connections['postgresql'] = db_config
            print("🗄️  Database connections configured")
        except Exception as e:
            print(f"⚠️  Database connection setup warning: {e}")
    
    async def execute_python(self, code: str, parameters: Dict[str, Any] = None,
                           timeout: int = 30) -> ExecutionOutput:
        """Execute Python code with safety restrictions"""
        parameters = parameters or {}
        execution_id = f"py_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        context = ExecutionContext(
            environment=ExecutionEnvironment.PYTHON,
            code=code,
            parameters=parameters,
            working_directory=self.working_directory,
            timeout_seconds=timeout,
            allowed_imports=list(self.allowed_packages)
        )
        
        try:
            # Create a safe execution environment
            safe_globals = self._create_safe_python_environment(parameters)
            safe_locals = {}
            
            # Execute the code
            result = await asyncio.wait_for(
                asyncio.to_thread(self._execute_python_safe, code, safe_globals, safe_locals),
                timeout=timeout
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.SUCCESS,
                output=str(result.get('output', '')),
                error_message=None,
                return_value=result.get('return_value'),
                execution_time=execution_time,
                timestamp=datetime.now(),
                resources_used={"memory_mb": 0}  # Placeholder
            )
            
        except asyncio.TimeoutError:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.TIMEOUT,
                output="",
                error_message=f"Execution timed out after {timeout} seconds",
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        except Exception as e:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.ERROR,
                output="",
                error_message=str(e),
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        
        self.execution_history.append(output)
        return output
    
    def _create_safe_python_environment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a safe Python execution environment"""
        safe_builtins = {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'min', 'max', 'sum', 'abs', 'round', 'sorted', 'reversed', 'enumerate',
            'zip', 'range', 'print', 'type', 'isinstance', 'hasattr', 'getattr'
        }
        
        # Create restricted __builtins__
        restricted_builtins = {name: __builtins__[name] for name in safe_builtins if name in __builtins__}
        
        # Add safe modules
        safe_globals = {
            '__builtins__': restricted_builtins,
            'json': json,
            'datetime': __import__('datetime'),
            'os': __import__('os'),  # Limited access
            'sys': __import__('sys'),
            'parameters': parameters,
            'agent_id': self.agent_id,
            'working_dir': self.working_directory
        }
        
        # Add database connection helper
        safe_globals['get_db_connection'] = self._get_db_connection_safe
        
        # Add file operations helper
        safe_globals['safe_file_operations'] = self._get_file_operations_helper()
        
        return safe_globals
    
    def _execute_python_safe(self, code: str, safe_globals: Dict[str, Any], safe_locals: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python code in a safe environment"""
        output_buffer = []
        
        # Capture print output
        class OutputCapture:
            def write(self, text):
                output_buffer.append(text)
            def flush(self):
                pass
        
        old_stdout = sys.stdout
        sys.stdout = OutputCapture()
        
        try:
            # Execute the code
            result = eval(compile(code, '<agent_code>', 'exec'), safe_globals, safe_locals)
            
            return {
                'return_value': result,
                'output': ''.join(output_buffer),
                'locals': {k: v for k, v in safe_locals.items() if not k.startswith('_')}
            }
        finally:
            sys.stdout = old_stdout
    
    def _get_db_connection_safe(self, db_type: str = 'postgresql'):
        """Safe database connection helper"""
        if db_type not in self.db_connections:
            raise ValueError(f"Database type {db_type} not configured")
        
        config = self.db_connections[db_type]
        if db_type == 'postgresql':
            return psycopg2.connect(**config)
        else:
            raise ValueError(f"Database type {db_type} not supported yet")
    
    def _get_file_operations_helper(self):
        """Get safe file operations helper"""
        class SafeFileOperations:
            def __init__(self, working_dir):
                self.working_dir = working_dir
            
            def read_file(self, filename: str) -> str:
                """Read a file from the working directory"""
                filepath = os.path.join(self.working_dir, filename)
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"File not found: {filename}")
                with open(filepath, 'r') as f:
                    return f.read()
            
            def write_file(self, filename: str, content: str):
                """Write content to a file in the working directory"""
                filepath = os.path.join(self.working_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
            
            def list_files(self) -> List[str]:
                """List files in the working directory"""
                return os.listdir(self.working_dir)
        
        return SafeFileOperations(self.working_directory)
    
    async def execute_sql(self, query: str, database: str = 'postgresql',
                         parameters: List[Any] = None) -> ExecutionOutput:
        """Execute SQL query safely"""
        parameters = parameters or []
        execution_id = f"sql_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        context = ExecutionContext(
            environment=ExecutionEnvironment.SQL,
            code=query,
            parameters={"database": database, "params": parameters},
            working_directory=self.working_directory,
            timeout_seconds=30
        )
        
        try:
            if database not in self.db_connections:
                raise ValueError(f"Database {database} not configured")
            
            config = self.db_connections[database]
            connection = psycopg2.connect(**config)
            
            try:
                cursor = connection.cursor()
                cursor.execute(query, parameters)
                
                # Handle different query types
                if query.strip().upper().startswith(('SELECT', 'WITH')):
                    results = cursor.fetchall()
                    column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                    output_data = {
                        'rows': results,
                        'columns': column_names,
                        'row_count': len(results)
                    }
                else:
                    connection.commit()
                    output_data = {
                        'affected_rows': cursor.rowcount,
                        'message': 'Query executed successfully'
                    }
                
                cursor.close()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                output = ExecutionOutput(
                    execution_id=execution_id,
                    context=context,
                    result=ExecutionResult.SUCCESS,
                    output=json.dumps(output_data, default=str),
                    error_message=None,
                    return_value=output_data,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    resources_used={}
                )
                
            finally:
                connection.close()
                
        except Exception as e:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.ERROR,
                output="",
                error_message=str(e),
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        
        self.execution_history.append(output)
        return output
    
    async def execute_bash(self, command: str, timeout: int = 30) -> ExecutionOutput:
        """Execute bash command safely"""
        execution_id = f"bash_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        context = ExecutionContext(
            environment=ExecutionEnvironment.BASH,
            code=command,
            parameters={},
            working_directory=self.working_directory,
            timeout_seconds=timeout
        )
        
        try:
            # Security check - block dangerous commands
            dangerous_patterns = ['rm -rf', 'sudo', 'chmod +x', 'curl', 'wget', 'ssh']
            if any(pattern in command.lower() for pattern in dangerous_patterns):
                raise PermissionError(f"Command blocked for security reasons: {command}")
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=self.working_directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if process.returncode == 0:
                output = ExecutionOutput(
                    execution_id=execution_id,
                    context=context,
                    result=ExecutionResult.SUCCESS,
                    output=stdout.decode('utf-8'),
                    error_message=stderr.decode('utf-8') if stderr else None,
                    return_value=process.returncode,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    resources_used={}
                )
            else:
                output = ExecutionOutput(
                    execution_id=execution_id,
                    context=context,
                    result=ExecutionResult.ERROR,
                    output=stdout.decode('utf-8'),
                    error_message=stderr.decode('utf-8'),
                    return_value=process.returncode,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    resources_used={}
                )
        
        except asyncio.TimeoutError:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.TIMEOUT,
                output="",
                error_message=f"Command timed out after {timeout} seconds",
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        except PermissionError as e:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.PERMISSION_DENIED,
                output="",
                error_message=str(e),
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        except Exception as e:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.ERROR,
                output="",
                error_message=str(e),
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        
        self.execution_history.append(output)
        return output
    
    async def execute_api_call(self, url: str, method: str = 'GET', 
                              headers: Dict[str, str] = None,
                              data: Dict[str, Any] = None) -> ExecutionOutput:
        """Execute API call safely"""
        import aiohttp
        
        execution_id = f"api_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        start_time = datetime.now()
        
        context = ExecutionContext(
            environment=ExecutionEnvironment.API,
            code=f"{method} {url}",
            parameters={"headers": headers, "data": data},
            working_directory=self.working_directory,
            timeout_seconds=30
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=headers, json=data, timeout=30
                ) as response:
                    response_text = await response.text()
                    
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    result_data = {
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'body': response_text
                    }
                    
                    result = ExecutionResult.SUCCESS if response.status < 400 else ExecutionResult.ERROR
                    
                    output = ExecutionOutput(
                        execution_id=execution_id,
                        context=context,
                        result=result,
                        output=response_text,
                        error_message=None if result == ExecutionResult.SUCCESS else f"HTTP {response.status}",
                        return_value=result_data,
                        execution_time=execution_time,
                        timestamp=datetime.now(),
                        resources_used={}
                    )
        
        except Exception as e:
            output = ExecutionOutput(
                execution_id=execution_id,
                context=context,
                result=ExecutionResult.ERROR,
                output="",
                error_message=str(e),
                return_value=None,
                execution_time=(datetime.now() - start_time).total_seconds(),
                timestamp=datetime.now(),
                resources_used={}
            )
        
        self.execution_history.append(output)
        return output
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics for this agent's hands"""
        if not self.execution_history:
            return {"message": "No executions yet"}
        
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e.result == ExecutionResult.SUCCESS])
        
        execution_types = {}
        for execution in self.execution_history:
            env = execution.context.environment.value
            execution_types[env] = execution_types.get(env, 0) + 1
        
        average_execution_time = sum(e.execution_time for e in self.execution_history) / total_executions
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "execution_types": execution_types,
            "average_execution_time": average_execution_time,
            "working_directory": self.working_directory
        }
    
    def get_recent_executions(self, limit: int = 10) -> List[ExecutionOutput]:
        """Get recent executions"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def clear_execution_history(self):
        """Clear execution history"""
        self.execution_history.clear()
        print(f"🧹 Cleared execution history for agent {self.agent_id}")


# Example specialized hand capabilities that can be inherited

class DataScienceHands(AgentHands):
    """Specialized hands for data science agents"""
    
    def __init__(self, agent_id: str, working_directory: str = None):
        super().__init__(agent_id, working_directory)
        
        # Add data science specific packages
        self.allowed_packages.update({
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'sklearn',
            'plotly', 'statsmodels', 'jupyter'
        })
    
    async def analyze_data(self, data_source: str, analysis_type: str) -> ExecutionOutput:
        """Perform data analysis with pre-built templates"""
        analysis_code = self._get_analysis_template(analysis_type, data_source)
        return await self.execute_python(analysis_code)
    
    def _get_analysis_template(self, analysis_type: str, data_source: str) -> str:
        """Get pre-built analysis templates"""
        templates = {
            "descriptive": f"""
import pandas as pd
import numpy as np

# Load data
data = pd.read_csv('{data_source}')

# Descriptive statistics
print("Data shape:", data.shape)
print("\\nData info:")
print(data.info())
print("\\nDescriptive statistics:")
print(data.describe())
print("\\nMissing values:")
print(data.isnull().sum())
            """,
            "correlation": f"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data  
data = pd.read_csv('{data_source}')

# Correlation analysis
correlation_matrix = data.corr()
print("Correlation matrix:")
print(correlation_matrix)

# Save correlation plot
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.title('Correlation Matrix')
plt.savefig('correlation_plot.png')
print("Correlation plot saved as correlation_plot.png")
            """
        }
        
        return templates.get(analysis_type, f"# Unknown analysis type: {analysis_type}")


class DeveloperHands(AgentHands):
    """Specialized hands for software development agents"""
    
    def __init__(self, agent_id: str, working_directory: str = None):
        super().__init__(agent_id, working_directory)
        
        # Add development specific packages
        self.allowed_packages.update({
            'git', 'pytest', 'black', 'flake8', 'mypy'
        })
    
    async def run_tests(self, test_path: str = "tests/") -> ExecutionOutput:
        """Run tests using pytest"""
        return await self.execute_bash(f"pytest {test_path} -v")
    
    async def format_code(self, file_path: str) -> ExecutionOutput:
        """Format code using black"""
        return await self.execute_bash(f"black {file_path}")
    
    async def git_commit(self, message: str, files: List[str] = None) -> ExecutionOutput:
        """Create git commit"""
        if files:
            add_command = f"git add {' '.join(files)}"
            await self.execute_bash(add_command)
        
        return await self.execute_bash(f'git commit -m "{message}"')