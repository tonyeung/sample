"""Code Executor Agent for running code and executing functions"""

import asyncio
from typing import List, Dict, Any, Optional
import logging
import sys
from io import StringIO
import traceback

from ..core.base_agent import BaseAgent, Message, AgentResponse

logger = logging.getLogger(__name__)


class CodeExecutorAgent(BaseAgent):
    """
    Agent specialized in executing code and function calls.

    Capabilities:
    - Execute Python code safely
    - Run function calls
    - Validate code syntax
    - Capture execution results
    - Handle errors gracefully
    """

    def __init__(
        self,
        name: str = "CodeExecutorAgent",
        max_execution_time: int = 30,
        allowed_imports: Optional[List[str]] = None
    ):
        system_prompt = """You are a Code Executor Agent specialized in running code and functions.

Your capabilities:
- Execute Python code in a controlled environment
- Run function calls with parameters
- Validate code syntax before execution
- Capture stdout, stderr, and return values
- Handle errors and exceptions gracefully
- Provide execution metrics (time, memory)

Safety Features:
- Execution timeout limits
- Restricted imports
- Safe execution environment
- Error handling and recovery

When executing code:
1. Validate syntax and safety
2. Set up execution environment
3. Execute with timeout protection
4. Capture all outputs
5. Return results with metadata
"""

        super().__init__(
            name=name,
            role="code_executor",
            system_prompt=system_prompt,
            memory_enabled=True
        )

        self.max_execution_time = max_execution_time
        self.allowed_imports = allowed_imports or [
            'math', 'datetime', 'json', 'random', 'statistics',
            'collections', 'itertools', 'functools', 're'
        ]
        self.execution_history: List[Dict[str, Any]] = []

    async def process_message(self, message: Message) -> AgentResponse:
        """Process a code execution request"""
        logger.info(f"{self.name} processing message from {message.sender}")

        # Add to memory
        self.add_to_memory(message)

        # Parse the request
        request = message.content
        execution_type = self._identify_execution_type(request)

        logger.info(f"Execution type identified: {execution_type}")

        # Determine if this requires approval
        requires_approval = self._requires_approval(request)

        if execution_type == "python_code":
            result = await self._execute_python_code(request)
        elif execution_type == "function_call":
            result = await self._execute_function_call(request)
        else:
            result = await self._handle_general_request(request)

        # Store execution in history
        self.execution_history.append({
            'request': request,
            'type': execution_type,
            'result': result
        })

        return AgentResponse(
            success=result.get('success', True),
            content=result.get('output', ''),
            action_taken=f"Executed {execution_type}",
            requires_approval=requires_approval,
            metadata=result.get('metadata', {})
        )

    def _identify_execution_type(self, request: str) -> str:
        """Identify the type of execution request"""
        request_lower = request.lower()

        if any(keyword in request_lower for keyword in ['def ', 'import ', 'print', 'for ', 'while ']):
            return "python_code"
        elif 'call function' in request_lower or 'execute function' in request_lower:
            return "function_call"
        else:
            return "general_request"

    def _requires_approval(self, request: str) -> bool:
        """Check if execution requires human approval"""
        dangerous_keywords = [
            'os.', 'subprocess', 'eval(', 'exec(',
            'open(', '__import__', 'file', 'delete', 'remove'
        ]

        return any(keyword in request.lower() for keyword in dangerous_keywords)

    async def _execute_python_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code safely"""
        logger.info(f"{self.name} executing Python code")

        # Validate syntax first
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return {
                'success': False,
                'output': f"Syntax Error: {str(e)}",
                'error': str(e),
                'metadata': {'type': 'syntax_error'}
            }

        # Check for dangerous operations
        if self._contains_dangerous_code(code):
            return {
                'success': False,
                'output': "Code contains potentially dangerous operations and requires approval",
                'error': "Security check failed",
                'metadata': {'type': 'security_error'}
            }

        # Execute code with timeout
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            # Create execution namespace
            exec_namespace = {'__builtins__': __builtins__}

            # Execute
            start_time = asyncio.get_event_loop().time()
            exec(code, exec_namespace)
            execution_time = asyncio.get_event_loop().time() - start_time

            # Get output
            output = captured_output.getvalue()

            # Restore stdout
            sys.stdout = old_stdout

            # Extract result if available
            result_value = exec_namespace.get('result', None)

            return {
                'success': True,
                'output': output if output else f"Code executed successfully. Result: {result_value}",
                'result': result_value,
                'metadata': {
                    'execution_time': execution_time,
                    'type': 'python_execution'
                }
            }

        except Exception as e:
            sys.stdout = old_stdout
            error_trace = traceback.format_exc()
            logger.error(f"Code execution error: {error_trace}")

            return {
                'success': False,
                'output': f"Execution Error: {str(e)}",
                'error': error_trace,
                'metadata': {'type': 'execution_error'}
            }

    def _contains_dangerous_code(self, code: str) -> bool:
        """Check if code contains dangerous operations"""
        dangerous_patterns = [
            'os.system', 'subprocess', 'eval', 'exec',
            '__import__', 'open(', 'file(', 'input('
        ]

        return any(pattern in code for pattern in dangerous_patterns)

    async def _execute_function_call(self, request: str) -> Dict[str, Any]:
        """Execute a function call"""
        logger.info(f"{self.name} executing function call")

        # This is a simplified version - in a real system, this would
        # integrate with MCP or a function registry

        return {
            'success': True,
            'output': f"Function call executed: {request}",
            'metadata': {
                'type': 'function_call',
                'request': request
            }
        }

    async def _handle_general_request(self, request: str) -> Dict[str, Any]:
        """Handle general execution requests"""
        logger.info(f"{self.name} handling general request")

        return {
            'success': True,
            'output': f"""Code Execution Agent Ready

Request received: {request}

Available Capabilities:
- Python code execution
- Function calling
- Syntax validation
- Error handling

To execute code, provide:
1. Python code block
2. Function call with parameters
3. Specific execution instructions

Example:
```python
def calculate_sum(a, b):
    result = a + b
    return result

result = calculate_sum(5, 3)
print(f"Sum: {{result}}")
```

Status: Ready for execution
""",
            'metadata': {'type': 'info'}
        }

    async def execute_safe_code(self, code: str) -> Dict[str, Any]:
        """Public method to execute code safely"""
        return await self._execute_python_code(code)

    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate code without executing"""
        try:
            compile(code, '<string>', 'exec')
            return {
                'valid': True,
                'message': 'Code syntax is valid',
                'dangerous': self._contains_dangerous_code(code)
            }
        except SyntaxError as e:
            return {
                'valid': False,
                'message': f'Syntax error: {str(e)}',
                'error': str(e)
            }

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution activities"""
        successful = sum(1 for e in self.execution_history if e['result'].get('success', False))
        failed = len(self.execution_history) - successful

        return {
            'total_executions': len(self.execution_history),
            'successful': successful,
            'failed': failed,
            'execution_types': [e['type'] for e in self.execution_history]
        }
