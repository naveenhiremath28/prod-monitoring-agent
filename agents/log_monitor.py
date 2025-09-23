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

load_dotenv()

class AdvancedLogMonitor:
    COMMON_LOG_LEVELS = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL', 'FATAL']

    def __init__(self, log_path: str, output_file: str = "errors.json", db_url: str = "postgresql://user:password@localhost/dbname"):
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

    def save_error(self, error_record: Dict):
        try:
            # Save to JSON file
            data = json.loads(self.output_file.read_text())
            data.append(error_record)
            self.output_file.write_text(json.dumps(data, indent=2))
            title = self.extract_clean_title(error_record['error_line'])
            print(f"\n\n\n\ntitle: {title}\n\n\n\n")
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
                # Create new issue
                issue_create = IssueCreate(
                    title=title,
                    description=error_record['error_context'],
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
    
    monitor = AdvancedLogMonitor(
        log_file,
        output_file=output_file,
        db_url=db_url
    )
    monitor.monitor()
