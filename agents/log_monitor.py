import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class AdvancedLogMonitor:
    COMMON_LOG_LEVELS = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL', 'FATAL']

    def __init__(self, log_path: str, output_file: str = "errors.json"):
        self.log_path = Path(log_path)
        self.last_position = 0
        self.total_processed = 0
        self.total_errors = 0
        self.output_file = Path(output_file)
        if not self.output_file.exists():
            self.output_file.write_text("[]")
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

    def save_error(self, error_record: Dict):
        try:
            data = json.loads(self.output_file.read_text())
            data.append(error_record)
            self.output_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving error: {e}")

    def extract_errors(self, lines: List[str]) -> List[Dict]:
        errors = []
        i = 0
        while i < len(lines):
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
                errors.append(error_record)
                self.save_error(error_record)
            else:
                i += 1
        return errors

    def monitor(self, interval: int = 5):
        print(f"Starting advanced log monitoring: {self.log_path}")
        try:
            while True:
                new_lines = self.read_new_lines()
                if new_lines:
                    self.total_processed += len(new_lines)
                    errors = self.extract_errors(new_lines)
                    for err in errors:
                        print(f"\nFound error ({err['level']}):")
                        print(f"Timestamp: {err['timestamp']}")
                        print(f"Source: {err['source']}")
                        print(f"Context:\n{err['error_context']}")
                        print("-"*80)
                        self.total_errors += 1
                    print(f"Processed: {self.total_processed}, Errors: {self.total_errors}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped gracefully.")


if __name__ == "__main__":
    log_file = "/Users/naveenvhiremath/Documents/testing/logs_testing/container.log"
    monitor = AdvancedLogMonitor(log_file)
    monitor.monitor()
