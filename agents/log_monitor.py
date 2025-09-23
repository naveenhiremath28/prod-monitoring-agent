import os
import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy import create_engine
from dotenv import load_dotenv

from api.controllers.services import IssueService
from api.schemas.schema import IssueCreate, IssueUpdate
from uuid import UUID
from agents.llm.ticket_generator import TicketGenerator

load_dotenv()

class AdvancedLogMonitor:
    COMMON_LOG_LEVELS = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL', 'FATAL']

    def __init__(self, log_path: str, output_file: str = "errors.json", db_url: str = "postgresql://user:password@localhost/dbname", 
                 use_llm: bool = True, llm_class: str = "AzureOpenAI", llm_params: Optional[Dict] = None):
        self.log_path = Path(log_path)
        self.last_position = 0
        self.total_processed = 0
        self.total_errors = 0
        self.failed_to_process = 0
        self.errors_found = 0
        self.errors_failed_to_insert = 0
        self.output_file = Path(output_file)
        if not self.output_file.exists():
            self.output_file.write_text("[]")
        engine = create_engine(db_url)
        self.issue_service = IssueService(engine)
        
        # LLM configuration
        self.use_llm = use_llm
        self.ticket_generator = None
        if self.use_llm:
            try:
                self.ticket_generator = TicketGenerator(
                    llm_class=llm_class,
                    model_params=llm_params or {}
                )
                print(f"LLM ticket generator initialized with {llm_class}")
            except Exception as e:
                print(f"Failed to initialize LLM ticket generator: {e}")
                print("Falling back to regex-based title extraction")
                self.use_llm = False
        
        # Remove ANSI colors
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        # Dynamic timestamp detection (flexible)
        self.timestamp_regex = re.compile(
            r'(\d{2,4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?)|'
            r'(\w{3} \d{1,2} \d{2}:\d{2}:\d{2})|'
            r'(\d{2}:\d{2}:\d{2}\.\d{3})'
        )

    def read_new_lines(self) -> List[str]:
        if not self.log_path.exists():
            return []
        with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(self.last_position)
            lines = f.readlines()
            self.last_position = f.tell()
            return lines

    def clean_line(self, line: str) -> str:
        return self.ansi_escape.sub('', line).rstrip()

    def detect_timestamp(self, line: str) -> Optional[str]:
        line_clean = self.clean_line(line)
        match = self.timestamp_regex.search(line_clean)
        if match:
            return next((g for g in match.groups() if g), None)
        return None

    def detect_log_level(self, line: str) -> str:
        line_clean = self.clean_line(line)
        for level in self.COMMON_LOG_LEVELS:
            if re.search(rf'\b{level}\b', line_clean, re.IGNORECASE):
                return level.upper()
        return 'UNKNOWN'

    def parse_timestamp(self, ts_str: Optional[str]) -> str:
        if not ts_str:
            return datetime.now().isoformat()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S,%f",
                    "%b %d %H:%M:%S", "%H:%M:%S.%f"):
            try:
                ts = datetime.strptime(ts_str.split(',')[0], fmt)
                return ts.isoformat()
            except:
                continue
        return datetime.now().isoformat()

    def extract_clean_title(self, error_line: str) -> str:
        """
        Extract a clean error title by removing timestamp, log level, and other metadata.
        Returns only the meaningful error message/issue name.
        """
        # Remove ANSI colors first
        clean_line = self.clean_line(error_line)
        
        # Remove timestamp if present
        clean_line = self.timestamp_regex.sub('', clean_line)
        
        # Remove log level patterns
        for level in self.COMMON_LOG_LEVELS:
            clean_line = re.sub(rf'\b{level}\b', '', clean_line, flags=re.IGNORECASE)
        
        # Remove common log prefixes and separators
        clean_line = re.sub(r'^[\[\]\s\-_|]+', '', clean_line)  # Remove leading brackets, dashes, pipes
        clean_line = re.sub(r'^[A-Za-z0-9._-]+\s*:', '', clean_line)  # Remove logger names
        clean_line = re.sub(r'^\s*\d+\s*', '', clean_line)  # Remove leading numbers
        clean_line = re.sub(r'^\s*[\[\](){}]+\s*', '', clean_line)  # Remove leading brackets/parentheses
        
        # Clean up whitespace
        clean_line = clean_line.strip()
        
        # If the line is empty or too short, use a generic title
        if len(clean_line) < 10:
            return "Error detected in logs"
        
        # Limit to 200 characters and ensure it ends properly
        if len(clean_line) > 200:
            clean_line = clean_line[:197] + "..."
        
        return clean_line

    def generate_ticket_content(self, error_record: Dict) -> tuple[str, str]:
        """
        Generate ticket title and description using LLM or fallback to regex
        
        Args:
            error_record: Dictionary containing error information
            
        Returns:
            Tuple of (title, description)
        """
        if self.use_llm and self.ticket_generator:
            try:
                title, description = self.ticket_generator.generate_ticket_content(
                    error_log=error_record['error_context'],
                    log_level=error_record['level'],
                    timestamp=error_record['timestamp'],
                    source=error_record['source']
                )
                print(f"Generated title with LLM: {title}")
                return title, description
            except Exception as e:
                print(f"LLM generation failed: {e}, falling back to regex")
                # Fall back to regex-based generation
                title = self.extract_clean_title(error_record['error_line'])
                description = error_record['error_context']
                return title, description
        else:
            # Use regex-based title extraction
            title = self.extract_clean_title(error_record['error_line'])
            description = error_record['error_context']
            return title, description

    def save_error(self, error_record: Dict):
        try:
            # Save to JSON file
            data = json.loads(self.output_file.read_text())
            data.append(error_record)
            self.output_file.write_text(json.dumps(data, indent=2))
            
            # Generate title and description using LLM or fallback to regex
            title, description = self.generate_ticket_content(error_record)
            print(f"\n\nGenerated title: {title}")
            print("====Description started====")
            print(f"\n\nGenerated description: {description}")
            print("====Description ended====")
            
            existing_issue = self.issue_service.get_issue_by_title(title)
            
            if existing_issue:
                # Update existing issue - only update occurrence and logs
                new_occurrence = existing_issue.get('occurrence', 0) + 1
                new_logs = existing_issue.get('issue_logs', []) + [error_record['error_context']]
                issue_update = IssueUpdate(
                    occurrence=new_occurrence,
                    issue_logs=new_logs
                )
                issue_id = existing_issue['id'] if isinstance(existing_issue['id'], UUID) else UUID(existing_issue['id'])
                self.issue_service.update_issue(issue_id, issue_update)
                print(f"Updated existing issue (occurrence: {issue_update.occurrence}), id: {issue_id}")
            else:
                # Create new issue with LLM-generated content
                issue_create = IssueCreate(
                    title=title,
                    description=description,
                    severity="high" if error_record['level'] in ['ERROR', 'CRITICAL', 'FATAL'] else "medium",
                    error_type="general",
                    application_type="Test",
                    occurrence=1,
                    issue_logs=[error_record['error_context']]
                )
                result = self.issue_service.create_issue(issue_create)
                print(f"Created new issue: id: {result.result.id}")
        except Exception as e:
            self.errors_failed_to_insert += 1
            print(f"Error saving error: {e}")

    def extract_errors(self, lines: List[str]) -> List[Dict]:
        errors = []
        i = 0
        while i < len(lines):
            try:
                line = lines[i]
                ts = self.detect_timestamp(line)
                level = self.detect_log_level(line)
                if level in ['ERROR', 'CRITICAL', 'FATAL']:
                    # Capture multi-line block until next timestamp
                    context_lines = [self.clean_line(line)]
                    i += 1
                    while i < len(lines) and not self.detect_timestamp(lines[i]):
                        context_lines.append(self.clean_line(lines[i]))
                        i += 1
                    context = '\n'.join(context_lines)
                    error_record = {
                        'timestamp': self.parse_timestamp(ts),
                        'level': level,
                        'error_line': context_lines[0],
                        'error_context': context,
                        'source': str(self.log_path)
                    }
                    print(f"\nFound error ({level}):")
                    print(f"Timestamp: {self.parse_timestamp(ts)}")
                    print(f"Source: {str(self.log_path)}")
                    print(f"Context:\n{context_lines[0]}")
                    errors.append(error_record)
                    self.errors_found += 1
                    self.save_error(error_record)
                    print("-"*80)
                else:
                    i += 1
            except Exception as e:
                self.failed_to_process += 1
                i += 1
        return errors

    def monitor(self, interval: int = 5):
        print(f"Starting advanced log monitoring: {self.log_path}")
        print(f"Issues will be created via service")
        try:
            while True:
                new_lines = self.read_new_lines()
                if new_lines:
                    self.total_processed += len(new_lines)
                    errors = self.extract_errors(new_lines)
                    self.total_errors += len(errors)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped gracefully.")
            # print(f"Final stats - Processed: {self.total_processed}, Failed to process: {self.failed_to_process}, Errors found: {self.errors_found}, Errors failed to insert: {self.errors_failed_to_insert}")


if __name__ == "__main__":
    log_file = os.getenv("LOG_FILE_PATH", "/Users/naveenvhiremath/Documents/testing/logs_testing/test.log")
    output_file = os.getenv("OUTPUT_FILE", "errors.json")
    db_url = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'prod_monitoring')}"
    
    # LLM configuration
    use_llm = os.getenv("USE_LLM", "true").lower() == "true"
    llm_class = os.getenv("LLM_CLASS", "AzureOpenAI")  # or "OpenAI"
    llm_params = {
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "500")),
    }
    
    monitor = AdvancedLogMonitor(
        log_file,
        output_file=output_file,
        db_url=db_url,
        use_llm=use_llm,
        llm_class=llm_class,
        llm_params=llm_params
    )
    monitor.monitor()
