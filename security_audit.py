#!/usr/bin/env python3
"""
🔒 Security Audit Script
בדיקת אבטחה לפני העלאה לגיט
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

class SecurityAuditor:
    """Security auditor for code repositories"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.issues = []
        self.warnings = []
        self.info = []

        # Patterns to search for sensitive data
        self.sensitive_patterns = {
            'API Keys': [
                r'api[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'apikey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'Tokens': [
                r'token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'access[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'Passwords': [
                r'password["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'passwd["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'pwd["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'Database Credentials': [
                r'db[_-]?password["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'database[_-]?url["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'Private Keys': [
                r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',
                r'private[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'AWS Credentials': [
                r'aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            ],
            'Email': [
                r'[\w\.-]+@[\w\.-]+\.\w+',
            ]
        }

        # Files that should be in .gitignore
        self.should_ignore = [
            '*.pyc',
            '__pycache__',
            '.env',
            '.DS_Store',
            'venv/',
            '*.db',
            '*.sqlite',
            '*.log',
            'execution_logs/',
            'backups/',
            'trades.db',
        ]

        # File extensions to scan
        self.scan_extensions = ['.py', '.env', '.json', '.yaml', '.yml', '.txt', '.md']

    def scan_file(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """Scan a single file for sensitive data"""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

                for category, patterns in self.sensitive_patterns.items():
                    for pattern in patterns:
                        for line_num, line in enumerate(lines, 1):
                            matches = re.finditer(pattern, line, re.IGNORECASE)
                            for match in matches:
                                # Skip if it looks like a placeholder or example
                                matched_text = match.group(0)
                                if any(placeholder in matched_text.lower() for placeholder in
                                      ['xxx', 'example', 'test', 'sample', 'placeholder', 'your_']):
                                    continue

                                findings.append((category, str(file_path), line_num))
        except Exception as e:
            self.warnings.append(f"Could not scan {file_path}: {e}")

        return findings

    def scan_directory(self):
        """Scan entire directory for security issues"""
        print(f"🔍 Scanning directory: {self.project_dir}")
        print("=" * 70)

        # Scan all relevant files
        all_findings = []
        scanned_count = 0

        for file_path in self.project_dir.rglob('*'):
            if file_path.is_file():
                # Skip certain directories
                if any(skip in str(file_path) for skip in ['venv', '__pycache__', '.git', 'node_modules']):
                    continue

                # Check extension
                if file_path.suffix in self.scan_extensions:
                    scanned_count += 1
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)

        print(f"✅ Scanned {scanned_count} files\n")

        # Report findings
        if all_findings:
            print("⚠️  POTENTIAL SENSITIVE DATA FOUND:")
            print("-" * 70)

            for category, file_path, line_num in all_findings:
                rel_path = Path(file_path).relative_to(self.project_dir)
                self.issues.append(f"{category} in {rel_path}:{line_num}")
                print(f"  ❌ {category}: {rel_path}:{line_num}")
        else:
            print("✅ No obvious sensitive data patterns found")

        print("\n")

    def check_gitignore(self):
        """Check if .gitignore exists and has necessary entries"""
        print("📝 Checking .gitignore...")
        print("-" * 70)

        gitignore_path = self.project_dir / '.gitignore'

        if not gitignore_path.exists():
            self.issues.append("No .gitignore file found!")
            print("  ❌ No .gitignore file found!")
            return

        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()

        missing = []
        for pattern in self.should_ignore:
            if pattern not in gitignore_content:
                missing.append(pattern)

        if missing:
            print("  ⚠️  Missing patterns in .gitignore:")
            for pattern in missing:
                self.warnings.append(f"Missing in .gitignore: {pattern}")
                print(f"    - {pattern}")
        else:
            print("  ✅ .gitignore looks good")

        print("\n")

    def check_untracked_files(self):
        """Check for files that should not be committed"""
        print("📁 Checking for sensitive files...")
        print("-" * 70)

        dangerous_files = []

        for file_path in self.project_dir.rglob('*'):
            if file_path.is_file():
                name = file_path.name.lower()

                # Check for common sensitive files
                if any(pattern in name for pattern in
                      ['.env', 'secret', 'credential', 'private', '.pem', '.key']):
                    if '.git' not in str(file_path):
                        dangerous_files.append(file_path)

        if dangerous_files:
            print("  ⚠️  Found potentially sensitive files:")
            for file_path in dangerous_files:
                rel_path = file_path.relative_to(self.project_dir)
                self.warnings.append(f"Sensitive file: {rel_path}")
                print(f"    - {rel_path}")
        else:
            print("  ✅ No obvious sensitive files found")

        print("\n")

    def check_database_files(self):
        """Check for database files that shouldn't be committed"""
        print("💾 Checking for database files...")
        print("-" * 70)

        db_files = []

        for file_path in self.project_dir.rglob('*.db'):
            if '.git' not in str(file_path):
                db_files.append(file_path)

        for file_path in self.project_dir.rglob('*.sqlite'):
            if '.git' not in str(file_path):
                db_files.append(file_path)

        if db_files:
            print("  ⚠️  Found database files:")
            for file_path in db_files:
                rel_path = file_path.relative_to(self.project_dir)
                self.info.append(f"Database file: {rel_path}")
                print(f"    - {rel_path}")
            print("  💡 Make sure these are in .gitignore!")
        else:
            print("  ✅ No database files found")

        print("\n")

    def generate_report(self):
        """Generate final security report"""
        print("=" * 70)
        print("📊 SECURITY AUDIT SUMMARY")
        print("=" * 70)

        print(f"\n🔴 Critical Issues: {len(self.issues)}")
        for issue in self.issues:
            print(f"  - {issue}")

        print(f"\n⚠️  Warnings: {len(self.warnings)}")
        for warning in self.warnings:
            print(f"  - {warning}")

        print(f"\n💡 Info: {len(self.info)}")
        for info in self.info:
            print(f"  - {info}")

        print("\n" + "=" * 70)

        if len(self.issues) == 0:
            print("✅ PASSED - Safe to commit!")
            print("=" * 70)
            return True
        else:
            print("❌ FAILED - Fix issues before committing!")
            print("=" * 70)
            return False

    def run_audit(self):
        """Run complete security audit"""
        print("\n🔒 SECURITY AUDIT")
        print("=" * 70)
        print(f"Project: {self.project_dir}")
        print("=" * 70)
        print("\n")

        self.check_gitignore()
        self.scan_directory()
        self.check_untracked_files()
        self.check_database_files()

        return self.generate_report()


def main():
    import sys

    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = os.getcwd()

    auditor = SecurityAuditor(project_dir)
    passed = auditor.run_audit()

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
