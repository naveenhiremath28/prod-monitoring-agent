"""
LLM-powered ticket title and description generator for log monitoring
"""
import json
from typing import Dict, Optional, Tuple
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from .llm_factory import LLMFactory

class TicketGenerator:
    """Service for generating ticket titles and descriptions using LLM"""
    
    def __init__(self, llm_class: str = "AzureOpenAI", model_params: Optional[dict] = None):
        """
        Initialize the ticket generator
        
        Args:
            llm_class: Type of LLM to use ("AzureOpenAI" or "OpenAI")
            model_params: Additional model parameters
        """
        print(f"\n\n\n\nCreating LLM instance with {llm_class}, model params: {model_params}")
        self.llm, self.token_counter = LLMFactory.create_llm(llm_class, model_params)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Setup system prompts for ticket generation"""
        self.title_prompt = """You are an expert at analyzing error logs and creating concise, descriptive ticket titles.

            Your task is to analyze the provided error log and generate a clear, actionable ticket title that:
            1. Is specific and descriptive (not generic)
            2. Identifies the main issue or component
            3. Is under 100 characters
            4. Uses proper capitalization and formatting
            5. Avoids technical jargon when possible

            Examples of good titles:
            - "Database connection timeout in user authentication service"
            - "Memory leak detected in payment processing module"
            - "SSL certificate validation failure for external API calls"
            - "Null pointer exception in order processing workflow"

            Examples of bad titles:
            - "Error in logs"
            - "System failure"
            - "Application crashed"
            - "Database error"

            Generate only the title, nothing else.
        """

        self.description_prompt = """You are an expert at analyzing error logs and creating detailed, actionable ticket descriptions.

            Your task is to analyze the provided error log and generate a **comprehensive, developer-friendly description** that can be used directly in a ticket. 

            The description should cover:
            - What happened (summary)
            - Likely cause of the error
            - Impact on systems/services
            - Any observations from the log that help understand the error

            **Formatting guidelines:**
            - Provide the description as a **continuous paragraph or a few well-structured paragraphs**.
            - Include all relevant technical details from the log.
            - Make it detailed and thorough, so that a developer reading it can understand the error and its impact.
            - Do **not** include headings, bullet points, or suggested actions.
            - Be specific and technical when appropriate.

            **Example output:**
            "The application failed to connect to the database due to exhausted connection pools. During peak traffic periods, long-running queries are consuming available connections, which prevents new API requests from accessing the database. This error affects all services relying on database queries, causing intermittent failures and delayed responses. The logs show frequent connection timeouts, indicating that the current connection pool size is insufficient for the traffic load. Additional details in the logs suggest that specific queries involving large datasets are particularly problematic, which contributes to the system instability observed during high load periods."
        """

    def generate_ticket_title(self, error_log: str, log_level: str = "ERROR") -> str:
        """
        Generate a ticket title from error log
        
        Args:
            error_log: The error log content
            log_level: Log level (ERROR, CRITICAL, FATAL, etc.)
            
        Returns:
            Generated ticket title
        """
        try:
            messages = [
                SystemMessage(content=self.title_prompt),
                HumanMessage(content=f"Log Level: {log_level}\n\nError Log:\n{error_log}")
            ]
            
            response = self.llm.invoke(messages)
            title = response.content.strip()
            
            # Fallback if title is too long or empty
            if len(title) > 200 or not title:
                title = self._fallback_title_generation(error_log, log_level)
            
            return title
            
        except Exception as e:
            print(f"Error generating title with LLM: {e}")
            return self._fallback_title_generation(error_log, log_level)
    
    def generate_ticket_description(self, error_log: str, log_level: str = "ERROR", 
                                  timestamp: str = "", source: str = "") -> str:
        """
        Generate a ticket description from error log
        
        Args:
            error_log: The error log content
            log_level: Log level (ERROR, CRITICAL, FATAL, etc.)
            timestamp: When the error occurred
            source: Source file or service
            
        Returns:
            Generated ticket description
        """
        try:
            context_info = f"Timestamp: {timestamp}\nSource: {source}\nLog Level: {log_level}\n\n"
            
            messages = [
                SystemMessage(content=self.description_prompt),
                HumanMessage(content=f"{context_info}Error Log:\n{error_log}")
            ]
            
            response = self.llm.invoke(messages)
            description = response.content.strip()
            print(f"\n\n\n\nGenerated description with LLM: {description}")
            # Fallback if description is empty
            if not description:
                description = self._fallback_description_generation(error_log, log_level, timestamp, source)
            
            return description
            
        except Exception as e:
            print(f"Error generating description with LLM: {e}")
            return self._fallback_description_generation(error_log, log_level, timestamp, source)
    
    def generate_ticket_content(self, error_log: str, log_level: str = "ERROR", 
                              timestamp: str = "", source: str = "") -> Tuple[str, str]:
        """
        Generate both title and description for a ticket
        
        Args:
            error_log: The error log content
            log_level: Log level (ERROR, CRITICAL, FATAL, etc.)
            timestamp: When the error occurred
            source: Source file or service
            
        Returns:
            Tuple of (title, description)
        """
        title = self.generate_ticket_title(error_log, log_level)
        description = self.generate_ticket_description(error_log, log_level, timestamp, source)
        
        return title, description
    
    def _fallback_title_generation(self, error_log: str, log_level: str) -> str:
        """Fallback title generation using simple heuristics"""
        # Extract first meaningful line
        lines = error_log.strip().split('\n')
        first_line = lines[0] if lines else ""
        
        # Simple keyword-based title generation
        if "timeout" in first_line.lower():
            return f"Timeout error detected ({log_level})"
        elif "connection" in first_line.lower():
            return f"Connection error detected ({log_level})"
        elif "memory" in first_line.lower():
            return f"Memory-related error detected ({log_level})"
        elif "database" in first_line.lower():
            return f"Database error detected ({log_level})"
        elif "authentication" in first_line.lower() or "auth" in first_line.lower():
            return f"Authentication error detected ({log_level})"
        elif "permission" in first_line.lower() or "access" in first_line.lower():
            return f"Permission/access error detected ({log_level})"
        else:
            return f"Error detected in logs ({log_level})"
    
    def _fallback_description_generation(self, error_log: str, log_level: str, 
                                       timestamp: str, source: str) -> str:
        """Fallback description generation"""
        return f"""**Error Summary**
        A {log_level} level error was detected in the system.

        **Timestamp**: {timestamp}
        **Source**: {source}
        **Log Level**: {log_level}

        **Error Details**:
        ```
        {error_log}
        ```

        **Next Steps**:
        1. Review the error log for specific error messages
        2. Check system resources and dependencies
        3. Investigate recent changes that might have caused this issue
        4. Monitor for similar errors in the future

    **Priority**: {'High' if log_level in ['CRITICAL', 'FATAL'] else 'Medium'}"""
    
    def get_token_usage(self) -> int:
        """Get total token usage for this session"""
        return getattr(self.token_counter, 'total_tokens', 0)
    
    def reset_token_counter(self):
        """Reset the token counter"""
        if hasattr(self.token_counter, 'total_tokens'):
            self.token_counter.total_tokens = 0
