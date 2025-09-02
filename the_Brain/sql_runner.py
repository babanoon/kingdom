#!/usr/bin/env python3
"""
Generic SQL Runner

A flexible tool to execute SQL files against PostgreSQL databases.
Configuration is loaded from config.json file.

Usage:
    python sql_runner.py <sql_file_path>
    python sql_runner.py create_brain_tables_corrected.sql
    python sql_runner.py --config custom_config.json my_queries.sql
    python sql_runner.py --delete-tables brain_tables_list.txt
"""

import psycopg2
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import os

class SQLRunner:
    def __init__(self, config_path='config.json'):
        """Initialize SQL Runner with configuration."""
        self.config = self.load_config(config_path)
        self.db_config = self.config['database']
        self.settings = self.config['settings']
        self.paths = self.config['paths']
        self.connection = None
        
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded from: {config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def connect_to_database(self):
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            if self.settings['verbose']:
                print(f"✅ Connected to PostgreSQL: {self.db_config['database']}@{self.db_config['host']}:{self.db_config['port']}")
            return self.connection
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            if self.settings['verbose']:
                print("🔌 Database connection closed")
    
    def read_sql_file(self, file_path):
        """Read SQL commands from file."""
        try:
            # Handle relative and absolute paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.paths['sql_files_dir'], file_path)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if self.settings['verbose']:
                print(f"📖 SQL file loaded: {file_path} ({len(content)} characters)")
            
            return content, file_path
        except FileNotFoundError:
            print(f"❌ SQL file not found: {file_path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading SQL file: {e}")
            sys.exit(1)
    
    def parse_sql_statements(self, sql_content):
        """Parse SQL content into individual statements."""
        # Split by semicolon but be smart about it
        statements = []
        current_statement = ""
        in_string = False
        escape_next = False
        
        for char in sql_content:
            if escape_next:
                current_statement += char
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                current_statement += char
                continue
                
            if char == "'" and not escape_next:
                in_string = not in_string
                
            if char == ';' and not in_string:
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
            else:
                current_statement += char
        
        # Add the last statement if it exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    def execute_sql_file(self, file_path):
        """Execute SQL file and return results."""
        sql_content, full_path = self.read_sql_file(file_path)
        statements = self.parse_sql_statements(sql_content)
        
        if self.settings['verbose']:
            print(f"🚀 Executing {len(statements)} SQL statements...")
        
        cursor = self.connection.cursor()
        results = {
            'successful': [],
            'failed': [],
            'total_statements': len(statements),
            'tables_created': [],
            'indexes_created': []
        }
        
        for i, statement in enumerate(statements):
            if not statement.strip():
                continue
                
            try:
                cursor.execute(statement)
                
                if self.settings['auto_commit']:
                    self.connection.commit()
                
                results['successful'].append(i + 1)
                
                # Extract information about what was created
                if 'CREATE TABLE' in statement.upper():
                    table_name = self.extract_table_name(statement)
                    results['tables_created'].append(table_name)
                    if self.settings['show_progress']:
                        print(f"✅ Created table: {table_name}")
                        
                elif 'CREATE INDEX' in statement.upper():
                    index_name = self.extract_index_name(statement)
                    results['indexes_created'].append(index_name)
                    if self.settings['show_progress']:
                        print(f"✅ Created index: {index_name}")
                
                elif 'DROP TABLE' in statement.upper():
                    table_name = self.extract_drop_table_name(statement)
                    if self.settings['show_progress']:
                        print(f"🗑️  Dropped table: {table_name}")
                        
            except psycopg2.Error as e:
                if not self.settings['auto_commit']:
                    self.connection.rollback()
                    
                results['failed'].append({
                    'statement_number': i + 1,
                    'error': str(e),
                    'statement_preview': statement[:100] + '...' if len(statement) > 100 else statement
                })
                
                print(f"❌ Error in statement {i + 1}: {e}")
                
                if self.settings['stop_on_error']:
                    break
        
        cursor.close()
        return results
    
    def extract_table_name(self, statement):
        """Extract table name from CREATE TABLE statement."""
        try:
            parts = statement.upper().split('IF NOT EXISTS')
            if len(parts) > 1:
                table_part = parts[1].split('(')[0].strip()
            else:
                table_part = statement.upper().split('CREATE TABLE')[1].split('(')[0].strip()
            return table_part.lower()
        except:
            return "unknown"
    
    def extract_index_name(self, statement):
        """Extract index name from CREATE INDEX statement."""
        try:
            parts = statement.upper().split('IF NOT EXISTS')
            if len(parts) > 1:
                index_part = parts[1].split('ON')[0].strip()
            else:
                index_part = statement.upper().split('CREATE INDEX')[1].split('ON')[0].strip()
            return index_part.lower()
        except:
            return "unknown"
    
    def extract_drop_table_name(self, statement):
        """Extract table name from DROP TABLE statement."""
        try:
            parts = statement.upper().split('IF EXISTS')
            if len(parts) > 1:
                table_part = parts[1].split()[0].strip()
            else:
                table_part = statement.upper().split('DROP TABLE')[1].split()[0].strip()
            return table_part.lower()
        except:
            return "unknown"
    
    def delete_tables_from_list(self, table_list_file):
        """Delete tables listed in a text file."""
        try:
            with open(table_list_file, 'r') as f:
                tables = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            cursor = self.connection.cursor()
            deleted_tables = []
            failed_deletions = []
            
            print(f"🗑️  Deleting {len(tables)} tables...")
            
            for table_name in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                    self.connection.commit()
                    deleted_tables.append(table_name)
                    if self.settings['show_progress']:
                        print(f"✅ Deleted table: {table_name}")
                except psycopg2.Error as e:
                    self.connection.rollback()
                    failed_deletions.append(table_name)
                    print(f"❌ Error deleting table {table_name}: {e}")
            
            cursor.close()
            return deleted_tables, failed_deletions
            
        except FileNotFoundError:
            print(f"❌ Table list file not found: {table_list_file}")
            sys.exit(1)
    
    def verify_tables(self, expected_tables=None):
        """Verify that tables exist in the database."""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"\n📊 Database Tables Report:")
            print(f"Total tables in database: {len(existing_tables)}")
            
            if expected_tables:
                matching_tables = [table for table in existing_tables if table in expected_tables]
                missing_tables = set(expected_tables) - set(existing_tables)
                
                print(f"Expected tables: {len(expected_tables)}")
                print(f"Found expected tables: {len(matching_tables)}")
                
                if missing_tables:
                    print(f"❌ Missing tables: {list(missing_tables)}")
                else:
                    print("✅ All expected tables found!")
            
            print(f"\n📋 All Tables:")
            for table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  • {table}: {count} rows")
            
            cursor.close()
            return existing_tables
            
        except psycopg2.Error as e:
            print(f"❌ Error verifying tables: {e}")
            cursor.close()
            return []
    
    def log_results(self, results, operation="SQL Execution"):
        """Log execution results."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n📈 {operation} Summary ({timestamp}):")
        print(f"✅ Successful statements: {len(results['successful'])}")
        print(f"❌ Failed statements: {len(results['failed'])}")
        
        if 'tables_created' in results and results['tables_created']:
            print(f"🏗️  Tables created: {len(results['tables_created'])}")
            
        if 'indexes_created' in results and results['indexes_created']:
            print(f"🔍 Indexes created: {len(results['indexes_created'])}")
        
        if results['failed']:
            print(f"\n❌ Failed Statements:")
            for failure in results['failed']:
                print(f"  Statement #{failure['statement_number']}: {failure['error']}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Execute SQL files against PostgreSQL database')
    parser.add_argument('sql_file', nargs='?', help='SQL file to execute')
    parser.add_argument('--config', '-c', default='config.json', help='Configuration file path')
    parser.add_argument('--delete-tables', help='Delete tables listed in specified file')
    parser.add_argument('--verify', action='store_true', help='Verify existing tables')
    parser.add_argument('--expected-tables', help='Comma-separated list of expected table names for verification')
    
    args = parser.parse_args()
    
    if not args.sql_file and not args.delete_tables and not args.verify:
        parser.print_help()
        sys.exit(1)
    
    print("🧠 Generic SQL Runner")
    print("=" * 50)
    
    # Initialize SQL Runner
    runner = SQLRunner(args.config)
    runner.connect_to_database()
    
    try:
        if args.delete_tables:
            # Delete tables from list
            deleted, failed = runner.delete_tables_from_list(args.delete_tables)
            print(f"\n📈 Deletion Summary:")
            print(f"✅ Deleted: {len(deleted)} tables")
            print(f"❌ Failed: {len(failed)} tables")
            
        elif args.sql_file:
            # Execute SQL file
            results = runner.execute_sql_file(args.sql_file)
            runner.log_results(results)
            
        if args.verify:
            # Verify tables
            expected = args.expected_tables.split(',') if args.expected_tables else None
            runner.verify_tables(expected)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        runner.disconnect()


if __name__ == "__main__":
    main()