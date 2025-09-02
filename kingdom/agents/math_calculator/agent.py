#!/usr/bin/env python3
"""
Math Calculator Agent

A specialized AI agent that combines Gemini AI reasoning with Python code execution
to solve mathematical problems, equations, and computational tasks. This agent can
understand complex mathematical queries in natural language and provide step-by-step
solutions with accurate calculations.

Agent Architecture:
- 🧠 Brain: Google Gemini for mathematical reasoning and problem analysis
- ✋ Hands: Python code execution for calculations and visualizations
- 👂 Ears: A2A messaging, routing from GeneralReceiver, direct API calls
- 👅 Tongue: Structured mathematical responses with code and explanations
- 👀 Eyes: Solution validation and accuracy verification
- 🦵 Legs: Optimized for computational workloads
- 🦷 Teeth: Code safety validation and execution sandboxing

Capabilities:
- Natural language mathematical problem understanding
- Python code generation for calculations
- Step-by-step solution explanations
- Support for algebra, calculus, statistics, geometry
- Data visualization and graphing
- Mathematical verification and validation
"""

import asyncio
import json
import logging
import re
import math
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import traceback

# Add project root to path
import sys
sys.path.append('/Users/ed/King/B2')

from kingdom.core.base_agent import BaseAgent, AgentType, AgentMessage, MessageType
from kingdom.core.genai_brain import GenAIBrain, GenAIProvider, ThinkingMode, AgentPersonality
from kingdom.core.agent_hands import AgentHands, ExecutionOutput, ExecutionEnvironment
from kingdom.core.agent_logging import get_agent_logger, log_task_start, log_task_complete, log_error
from kingdom.service.agent_service import ServiceAgent

@dataclass
class MathSolution:
    """Represents a complete mathematical solution"""
    problem: str
    solution_steps: List[str]
    python_code: str
    execution_result: Any
    final_answer: str
    confidence: float
    execution_time_ms: int
    has_visualization: bool = False
    visualization_data: Optional[Dict] = None

class MathCalculatorAgent(ServiceAgent):
    """
    Math Calculator Agent - Specialized mathematical problem solver
    
    Combines Gemini AI for mathematical reasoning with Python execution
    for accurate calculations and step-by-step solutions.
    """
    
    def __init__(self, agent_id: str, agent_type: str = "math_calculator"):
        super().__init__(agent_id, agent_type)
        
        # Agent configuration
        self.config = self._load_config()
        
        # Initialize GenAI brain with mathematical personality
        self.brain = GenAIBrain(
            agent_id=agent_id,
            personality=self._get_mathematical_personality(),
            primary_provider=GenAIProvider.OPENAI
        )
        
        # Initialize agent hands for code execution
        self.hands = AgentHands(
            agent_id=agent_id,
            working_directory=f"./kingdom/agents/math_calculator/workspace"
        )
        
        # Mathematical solution history
        self.solution_history = []
        
        # Mathematical constants and functions
        self.math_constants = self._load_math_constants()
        
        # Problem type classifiers
        self.problem_types = self._load_problem_types()

        # Setup centralized logging
        self.agent_logger = get_agent_logger(agent_id, "local")  # Assume local for now
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            with open('/Users/ed/King/B2/kingdom/agents/math_calculator/config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "max_solution_history": 20,
                "execution_timeout": 60,
                "enable_visualization": True,
                "precision_digits": 10,
                "safety_level": "high"
            }
    
    def _get_mathematical_personality(self) -> AgentPersonality:
        """Define mathematical agent personality"""
        return AgentPersonality(
            name="MathCalculator",
            role="Mathematical Problem Solver and Calculator",
            personality_traits=[
                "Precise and accurate",
                "Methodical and step-by-step",
                "Explains reasoning clearly",
                "Validates solutions",
                "Educational and informative"
            ],
            expertise_areas=[
                "Algebra and equations",
                "Calculus and derivatives",
                "Statistics and probability", 
                "Geometry and trigonometry",
                "Number theory",
                "Linear algebra",
                "Data analysis and visualization"
            ],
            communication_style="Clear mathematical explanations with step-by-step solutions",
            preferred_thinking_mode=ThinkingMode.ANALYTICAL,
            system_prompt_template="You are a precise mathematical problem solver.",
            temperature=0.3,
            max_tokens=3000
        )
    
    def _get_allowed_imports(self) -> List[str]:
        """Define allowed Python imports for mathematical calculations"""
        return [
            "math", "numpy", "scipy", "sympy", "matplotlib", "pandas",
            "statistics", "decimal", "fractions", "cmath", "random"
        ]
    
    def _load_math_constants(self) -> Dict[str, float]:
        """Load mathematical constants"""
        return {
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "golden_ratio": (1 + math.sqrt(5)) / 2,
            "sqrt2": math.sqrt(2),
            "sqrt3": math.sqrt(3),
            "euler_gamma": 0.5772156649015329
        }
    
    def _load_problem_types(self) -> Dict[str, Dict[str, Any]]:
        """Load mathematical problem type classifiers"""
        return {
            "arithmetic": {
                "keywords": ["add", "subtract", "multiply", "divide", "calculate", "compute"],
                "complexity": "basic",
                "requires_code": False
            },
            "algebra": {
                "keywords": ["solve", "equation", "variable", "x", "y", "polynomial"],
                "complexity": "intermediate", 
                "requires_code": True
            },
            "calculus": {
                "keywords": ["derivative", "integral", "limit", "calculus", "differentiate", "integrate"],
                "complexity": "advanced",
                "requires_code": True
            },
            "statistics": {
                "keywords": ["mean", "median", "standard deviation", "probability", "statistics"],
                "complexity": "intermediate",
                "requires_code": True
            },
            "geometry": {
                "keywords": ["area", "volume", "perimeter", "angle", "triangle", "circle"],
                "complexity": "intermediate",
                "requires_code": True
            },
            "finance": {
                "keywords": ["interest", "compound", "loan", "investment", "present value"],
                "complexity": "intermediate", 
                "requires_code": True
            }
        }
    
    async def _handle_task(self, task) -> Any:
        """Handle tasks for MathCalculator agent"""
        task_type = task.task_type
        payload = task.payload

        # Log task start
        log_task_start(self.agent_id, task.task_id, task_type, "local")
        self.agent_logger.log("task_received", f"Processing mathematical {task_type}", {
            "task_id": task.task_id,
            "payload_keys": list(payload.keys()) if payload else [],
            "problem_preview": payload.get('problem', '')[:100] if 'problem' in payload else ""
        })

        try:
            if task_type == "solve_math_problem":
                result = await self._handle_math_problem(payload)
            elif task_type == "routed_request":
                result = await self._handle_routed_math_request(payload)
            elif task_type == "validate_solution":
                result = await self._handle_solution_validation(payload)
            elif task_type == "get_solution_history":
                result = await self._handle_get_solution_history(payload)
            else:
                result = {"error": f"Unknown task type: {task_type}"}

            # Log task completion
            log_task_complete(self.agent_id, task.task_id, result, "local")
            self.agent_logger.log("task_completed", f"Mathematical {task_type} completed", {
                "task_id": task.task_id,
                "success": result.get('success', False) if isinstance(result, dict) else True,
                "problem_length": len(payload.get('problem', '')) if 'problem' in payload else 0
            })

            return result

        except Exception as e:
            # Log error
            log_error(self.agent_id, task_type, e, "local")
            self.agent_logger.log("task_error", f"Mathematical {task_type} failed", {
                "task_id": task.task_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "problem": payload.get('problem', '')[:200] if 'problem' in payload else ""
            })
            return {"error": str(e), "success": False}
    
    async def _handle_math_problem(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct mathematical problem solving"""
        problem = payload.get('problem', '')
        show_steps = payload.get('show_steps', True)
        enable_visualization = payload.get('enable_visualization', self.config.get('enable_visualization', True))
        
        if not problem:
            return {"error": "No problem provided", "success": False}
        
        try:
            # Fast-path: try to solve simple arithmetic locally without LLM
            fast_start = datetime.now()
            local_result = self._try_local_arithmetic(problem)
            if local_result is not None:
                execution_time = int((datetime.now() - fast_start).total_seconds() * 1000)
                self.agent_logger.log(
                    "local_solver_used",
                    "Solved arithmetic locally without LLM",
                    {
                        "problem": problem,
                        "final_answer": local_result,
                        "execution_time_ms": execution_time
                    }
                )
                return {
                    "success": True,
                    "problem": problem,
                    "solution_steps": [
                        "1. Detected a simple arithmetic expression",
                        "2. Evaluated expression safely using local parser",
                        f"3. Final answer computed: {local_result}"
                    ],
                    "python_code": None,
                    "final_answer": str(local_result),
                    "confidence": 1.0,
                    "execution_time_ms": execution_time,
                    "has_visualization": False,
                    "agent_id": self.agent_id
                }

            solution = await self._solve_mathematical_problem(problem, show_steps, enable_visualization)
            
            # Store in solution history
            self.solution_history.append({
                "problem": problem,
                "solution": solution,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            })
            
            # Maintain history size
            if len(self.solution_history) > self.config.get('max_solution_history', 20):
                self.solution_history = self.solution_history[-self.config.get('max_solution_history', 20):]
            
            return {
                "success": True,
                "problem": solution.problem,
                "solution_steps": solution.solution_steps,
                "python_code": solution.python_code,
                "final_answer": solution.final_answer,
                "confidence": solution.confidence,
                "execution_time_ms": solution.execution_time_ms,
                "has_visualization": solution.has_visualization,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            self.logger.error(f"Error solving math problem: {e}")
            return {
                "success": False,
                "error": str(e),
                "problem": problem,
                "agent_id": self.agent_id
            }

    def _try_local_arithmetic(self, text: str):
        """Evaluate simple arithmetic expressions safely. Returns a number or None."""
        import ast
        import operator as op

        # Allowed operators
        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.USub: op.neg,
            ast.UAdd: op.pos,
            ast.FloorDiv: op.floordiv,
            ast.Mod: op.mod,
            ast.LShift: op.lshift,
            ast.RShift: op.rshift,
            ast.BitOr: op.or_,
            ast.BitAnd: op.and_,
            ast.BitXor: op.xor
        }

        # Extract a likely expression (strip leading words like 'what is', 'solve')
        lowered = text.lower().strip()
        for prefix in ["what is", "what's", "solve", "calculate", "compute", "please calculate", "can you solve"]:
            if lowered.startswith(prefix):
                text = text[len(prefix):].strip().lstrip(':').lstrip()
                break

        # Quick validation: must contain digits and an arithmetic operator
        if not any(ch.isdigit() for ch in text) or not any(opr in text for opr in ['+', '-', '*', '/', '(', ')']):
            return None

        try:
            node = ast.parse(text, mode='eval')
        except Exception:
            return None

        def _eval(n):
            if isinstance(n, ast.Expression):
                return _eval(n.body)
            if isinstance(n, ast.Num):  # Python <3.8
                return n.n
            if hasattr(ast, 'Constant') and isinstance(n, ast.Constant):  # Python 3.8+
                if isinstance(n.value, (int, float)):
                    return n.value
                return None
            if isinstance(n, ast.BinOp) and type(n.op) in operators:
                left = _eval(n.left)
                right = _eval(n.right)
                return operators[type(n.op)](left, right)
            if isinstance(n, ast.UnaryOp) and type(n.op) in operators:
                operand = _eval(n.operand)
                return operators[type(n.op)](operand)
            # Disallow everything else for safety
            raise ValueError("Unsupported expression")

        try:
            value = _eval(node)
            # Normalize ints when applicable
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value
        except Exception:
            return None
    
    async def _handle_routed_math_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mathematical requests routed from GeneralReceiver"""
        original_message = payload.get('original_message', '')
        sender = payload.get('sender', 'unknown')
        return_address = payload.get('routed_by', '')
        
        self.logger.info(f"Processing routed math request from {sender}: {original_message}")
        
        # Extract mathematical problem from the message
        math_problem = await self._extract_math_problem_from_message(original_message)
        
        # Solve the problem
        result = await self._handle_math_problem({"problem": math_problem})
        
        # Send response back to routing agent if specified
        if return_address:
            await self.send_a2a_message(return_address, {
                "type": "specialist_response",
                "original_sender": sender,
                "problem": math_problem,
                "solution": result,
                "specialist": "math_calculator"
            })
        
        return result
    
    async def _solve_mathematical_problem(self, problem: str, show_steps: bool = True, 
                                        enable_visualization: bool = True) -> MathSolution:
        """Solve a mathematical problem using Gemini AI + Python execution"""
        start_time = datetime.now()
        
        # Classify problem type
        problem_type = self._classify_problem_type(problem)
        
        # Use Gemini to analyze the problem and generate solution approach
        analysis_prompt = self._create_analysis_prompt(problem, problem_type)
        
        ai_analysis = await self.brain.think(
            input_text=analysis_prompt,
            context={"problem_type": problem_type, "show_steps": show_steps},
            thinking_mode=ThinkingMode.ANALYTICAL
        )

        # Extract Python code from AI response
        python_code = self._extract_python_code(ai_analysis.raw_response)
        
        # Execute the Python code
        execution_result = await self._execute_math_code(python_code)
        
        # Generate step-by-step explanation
        if show_steps:
            steps = await self._generate_solution_steps(problem, ai_analysis.raw_response, execution_result)
        else:
            steps = ["Solution calculated using Python execution"]

        # Extract final answer
        final_answer = self._extract_final_answer(execution_result, ai_analysis.raw_response)
        
        # Calculate execution time
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Create visualization if applicable
        has_viz, viz_data = await self._create_visualization_if_needed(
            problem, python_code, execution_result, enable_visualization
        )
        
        return MathSolution(
            problem=problem,
            solution_steps=steps,
            python_code=python_code,
            execution_result=execution_result.output if execution_result.result.name == 'SUCCESS' else None,
            final_answer=final_answer,
            confidence=ai_analysis.confidence,
            execution_time_ms=execution_time,
            has_visualization=has_viz,
            visualization_data=viz_data
        )
    
    def _classify_problem_type(self, problem: str) -> str:
        """Classify the type of mathematical problem"""
        problem_lower = problem.lower()
        scores = {}
        
        for prob_type, info in self.problem_types.items():
            score = sum(1 for keyword in info["keywords"] if keyword in problem_lower)
            if score > 0:
                scores[prob_type] = score
        
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        return "general"
    
    def _create_analysis_prompt(self, problem: str, problem_type: str) -> str:
        """Create prompt for mathematical problem analysis"""
        return f"""
You are a mathematical problem solver. Analyze this {problem_type} problem and provide a solution approach.

Problem: {problem}

Please:
1. Identify what type of mathematical problem this is
2. Explain your approach to solving it
3. Write Python code to solve the problem step by step
4. Include proper mathematical libraries (numpy, sympy, matplotlib as needed)
5. Add comments explaining each step
6. Make sure the code produces a clear final answer

Format your response with the Python code clearly marked between ```python and ``` tags.

Mathematical constants available: {list(self.math_constants.keys())}

Focus on accuracy and clarity in your solution.
"""
    
    def _extract_python_code(self, ai_response: str) -> str:
        """Extract Python code from AI response"""
        # Look for code blocks
        pattern = r'```python\n(.*?)\n```'
        matches = re.findall(pattern, ai_response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Fallback: look for any code-like content
        lines = ai_response.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if any(keyword in line for keyword in ['import ', 'def ', 'print(', '=', 'math.']):
                in_code = True
            if in_code:
                code_lines.append(line)
            if line.strip() == '' and in_code and len(code_lines) > 5:
                break
        
        return '\n'.join(code_lines) if code_lines else "# No code generated"
    
    async def _execute_math_code(self, python_code: str) -> ExecutionOutput:
        """Execute mathematical Python code safely"""
        # Add mathematical imports and constants to code
        enhanced_code = self._enhance_code_with_math_setup(python_code)
        
        try:
            result = await self.hands.execute_python(
                code=enhanced_code,
                timeout=self.config.get('execution_timeout', 60)
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing math code: {e}")
            return ExecutionOutput(
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=0
            )
    
    def _enhance_code_with_math_setup(self, code: str) -> str:
        """Enhance code with mathematical imports and constants"""
        setup_code = """
import math
import numpy as np
import matplotlib.pyplot as plt
from decimal import Decimal, getcontext
import statistics
from fractions import Fraction

# Set high precision for calculations
getcontext().prec = 28

# Mathematical constants
pi = math.pi
e = math.e
tau = math.tau
golden_ratio = (1 + math.sqrt(5)) / 2

# Helper functions
def round_to_precision(value, digits=10):
    if isinstance(value, (int, float)):
        return round(value, digits)
    return value

def format_answer(value):
    if isinstance(value, (int, float)):
        if abs(value - round(value)) < 1e-10:
            return int(round(value))
        else:
            return round(value, 10)
    return value

"""
        return setup_code + "\n" + code + "\n\nprint('Final calculation completed')"
    
    async def _generate_solution_steps(self, problem: str, ai_analysis: str, 
                                     execution_result: ExecutionOutput) -> List[str]:
        """Generate step-by-step solution explanation"""
        steps_prompt = f"""
Based on this mathematical problem and solution, provide clear step-by-step explanation:

Problem: {problem}
Analysis: {ai_analysis}
Execution Result: {execution_result.output if execution_result.result.name == 'SUCCESS' else 'Error in execution'}

Provide numbered steps that explain:
1. What the problem is asking
2. The mathematical approach used
3. Key calculations performed
4. The final answer and what it means

Make it educational and easy to understand.
"""
        
        try:
            steps_response = await self.brain.think(
                input_text=steps_prompt,
                context={"task": "explanation"},
                thinking_mode=ThinkingMode.ANALYTICAL
            )
            
            # Parse steps from response
            lines = steps_response.raw_response.split('\n')
            steps = []
            for line in lines:
                line = line.strip()
                if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                    steps.append(line)
            
            return steps if steps else ["Solution completed using mathematical computation"]
            
        except Exception as e:
            self.logger.error(f"Error generating solution steps: {e}")
            return ["Solution calculated successfully"]
    
    def _extract_final_answer(self, execution_result: ExecutionOutput, ai_analysis: str) -> str:
        """Extract the final answer from execution results"""
        if execution_result.result.name != 'SUCCESS':
            return "Error in calculation"
        
        output = str(execution_result.output) if execution_result.output else ""
        
        # Look for final answer patterns in output
        answer_patterns = [
            r'Final answer[:\s]+([^\n]+)',
            r'Result[:\s]+([^\n]+)',
            r'Answer[:\s]+([^\n]+)',
            r'=\s*([0-9]+\.?[0-9]*)',
            r'([0-9]+\.?[0-9]*)\s*$'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: try to extract from AI analysis
        if "=" in ai_analysis:
            parts = ai_analysis.split("=")
            if len(parts) > 1:
                potential_answer = parts[-1].strip().split()[0]
                try:
                    float(potential_answer)
                    return potential_answer
                except ValueError:
                    pass
        
        return "Calculation completed successfully"
    
    async def _create_visualization_if_needed(self, problem: str, code: str, 
                                            execution_result: ExecutionOutput,
                                            enable_viz: bool) -> Tuple[bool, Optional[Dict]]:
        """Create visualization for mathematical problems if applicable"""
        if not enable_viz or execution_result.result.name != 'SUCCESS':
            return False, None
        
        # Check if problem benefits from visualization
        viz_keywords = ["graph", "plot", "function", "equation", "data", "distribution"]
        if not any(keyword in problem.lower() for keyword in viz_keywords):
            return False, None
        
        try:
            # Generate visualization code
            viz_code = await self._generate_visualization_code(problem, code)
            if viz_code:
                viz_result = await self.hands.execute_python(viz_code, timeout=30)
                if viz_result.result.name == 'SUCCESS':
                    return True, {"visualization_code": viz_code, "result": viz_result.output}
        
        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
        
        return False, None
    
    async def _generate_visualization_code(self, problem: str, original_code: str) -> str:
        """Generate Python code for problem visualization"""
        viz_prompt = f"""
Create a Python matplotlib visualization for this mathematical problem:

Problem: {problem}
Original Code: {original_code}

Generate clean matplotlib code that creates an appropriate visualization.
Include proper labels, title, and formatting.
Return only the Python code for the visualization.
"""
        
        try:
            viz_response = await self.brain.think(
                input_text=viz_prompt,
                context={"task": "visualization"},
                thinking_mode=ThinkingMode.PRACTICAL
            )
            
            return self._extract_python_code(viz_response.raw_response)
        
        except Exception as e:
            self.logger.error(f"Error generating visualization code: {e}")
            return ""
    
    async def _extract_math_problem_from_message(self, message: str) -> str:
        """Extract mathematical problem from natural language message"""
        # Use AI to extract/reformat the mathematical problem
        extraction_prompt = f"""
Extract the mathematical problem from this message and reformat it clearly:

Message: {message}

Provide just the mathematical problem in a clear, solvable format.
If it's a word problem, include all necessary information.
"""
        
        try:
            extraction_result = await self.brain.think(
                input_text=extraction_prompt,
                context={"task": "problem_extraction"},
                thinking_mode=ThinkingMode.ANALYTICAL
            )
            return extraction_result.raw_response.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting math problem: {e}")
            return message  # Fallback to original message
    
    async def _handle_solution_validation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a mathematical solution"""
        solution = payload.get('solution', '')
        problem = payload.get('problem', '')
        
        try:
            validation_prompt = f"""
Validate this mathematical solution:

Problem: {problem}
Solution: {solution}

Check if:
1. The solution method is correct
2. The calculations are accurate  
3. The final answer is reasonable
4. Any errors or improvements needed

Provide validation result and confidence score.
"""
            
            validation_result = await self.brain.think(
                input_text=validation_prompt,
                context={"task": "validation"},
                thinking_mode=ThinkingMode.ANALYTICAL
            )
            
            return {
                "success": True,
                "validation_result": validation_result.raw_response,
                "confidence": validation_result.confidence,
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_get_solution_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get solution history for this agent"""
        limit = payload.get('limit', 10)
        
        return {
            "success": True,
            "solution_history": self.solution_history[-limit:],
            "total_solutions": len(self.solution_history),
            "agent_id": self.agent_id
        }

    async def _handle_a2a_message(self, message):
        """Handle A2A messages from other agents"""
        print(f"🔍 MATH DEBUG: MathCalculator {self.agent_id} received A2A message: {message}")
        self.logger.info(f"🔍 MATH DEBUG: MathCalculator {self.agent_id} received A2A message from {message.get('sender', 'unknown')}")
        payload = message['payload']
        message_type = payload.get('type', 'unknown')

        self.logger.info(f"Received A2A message type: {message_type} from {message['sender']}")

        if message_type == "routed_request":
            print(f"🔍 MATH DEBUG: Processing routed_request in {self.agent_id}")
            self.logger.info(f"🔍 MATH DEBUG: Processing routed_request in {self.agent_id}")
            await self._handle_routed_request(message)
        elif message_type == "math_request":
            await self._handle_a2a_math_request(message)
        elif message_type == "validation_request":
            await self._handle_a2a_validation_request(message)
        else:
            self.logger.warning(f"Unknown A2A message type: {message_type}")

    async def _handle_routed_request(self, message):
        """Handle routed requests from general_receiver agent"""
        payload = message['payload']
        routed_payload = payload.get('payload', {})
        sender = message['sender']
        return_address = routed_payload.get('routed_by')

        original_message = routed_payload.get('original_message', '')
        workflow_id = routed_payload.get('workflow_id')

        self.logger.info(f"Processing routed math request from {sender}: {original_message}")

        try:
            # Extract and solve the math problem
            math_problem = await self._extract_math_problem_from_message(original_message)
            result = await self._handle_math_problem({"problem": math_problem})

            # Send response back to the routing agent
            response_payload = {
                "type": "specialist_response",
                "original_sender": routed_payload.get('sender'),
                "problem": math_problem,
                "solution": result,
                "specialist": "math_calculator",
                "workflow_id": workflow_id
            }

            await self.send_a2a_message(return_address, response_payload)
            self.logger.info(f"Sent math solution back to {return_address}")

        except Exception as e:
            self.logger.error(f"Error processing routed math request: {e}")
            # Send error response back
            error_payload = {
                "type": "specialist_response",
                "original_sender": routed_payload.get('sender'),
                "error": str(e),
                "specialist": "math_calculator",
                "workflow_id": workflow_id
            }
            await self.send_a2a_message(return_address, error_payload)

    async def get_agent_stats(self) -> Dict[str, Any]:
        """Get detailed agent statistics"""
        base_stats = await self.get_status()
        
        return {
            **base_stats,
            "solutions_completed": len(self.solution_history),
            "problem_types_supported": list(self.problem_types.keys()),
            "mathematical_constants_available": list(self.math_constants.keys()),
            "visualization_enabled": self.config.get('enable_visualization', True),
            "execution_timeout": self.config.get('execution_timeout', 60),
            "genai_provider": "gemini"
        }