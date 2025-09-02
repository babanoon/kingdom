#!/usr/bin/env python3
"""
Brain Database Table Creation Script

This script creates all the necessary tables for the Brain knowledge management system.
It safely creates tables using CREATE TABLE IF NOT EXISTS to avoid conflicts.
"""

import psycopg2
import os
import sys
from pathlib import Path

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 9876,
    'database': 'general2613',
    'user': 'kadmin',
    'password': 'securepasswordkossher123'
}

def connect_to_database():
    """Establish connection to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Successfully connected to PostgreSQL database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error connecting to PostgreSQL database: {e}")
        sys.exit(1)

def read_sql_file(file_path):
    """Read SQL commands from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        sys.exit(1)

def execute_sql_commands(conn, sql_content):
    """Execute SQL commands and handle errors gracefully."""
    cursor = conn.cursor()
    
    # Split SQL content into individual statements
    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    successful_tables = []
    failed_tables = []
    
    for i, statement in enumerate(statements):
        if statement.strip():
            try:
                cursor.execute(statement)
                conn.commit()
                
                # Extract table name from CREATE TABLE statement
                if 'CREATE TABLE' in statement.upper():
                    table_name = statement.split('IF NOT EXISTS')[-1].split('(')[0].strip()
                    successful_tables.append(table_name)
                    print(f"✅ Created table: {table_name}")
                elif 'CREATE INDEX' in statement.upper():
                    index_name = statement.split('IF NOT EXISTS')[-1].split('ON')[0].strip()
                    print(f"✅ Created index: {index_name}")
                
            except psycopg2.Error as e:
                conn.rollback()
                failed_tables.append(f"Statement {i+1}")
                print(f"❌ Error executing statement {i+1}: {e}")
                print(f"Statement: {statement[:100]}...")
    
    cursor.close()
    return successful_tables, failed_tables

def verify_tables(conn):
    """Verify that all expected tables were created."""
    cursor = conn.cursor()
    
    expected_tables = [
        'core_entities', 'contexts', 'persons', 'organizations', 'places', 
        'events', 'conversations', 'tasks', 'projects', 'objects', 
        'media_documents', 'ideas', 'knowledge_facts', 'preferences', 
        'routines', 'health_episodes', 'travels', 'transactions', 
        'device_sessions', 'time_periods'
    ]
    
    try:
        # Query to get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        brain_tables = [table for table in existing_tables if table in expected_tables]
        
        print(f"\n📊 Table Verification Report:")
        print(f"Expected tables: {len(expected_tables)}")
        print(f"Created tables: {len(brain_tables)}")
        
        if len(brain_tables) == len(expected_tables):
            print("✅ All expected tables created successfully!")
        else:
            missing_tables = set(expected_tables) - set(brain_tables)
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
        
        print(f"\n📋 Created Brain Tables:")
        for table in sorted(brain_tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  • {table}: {count} rows")
        
        cursor.close()
        return brain_tables
        
    except psycopg2.Error as e:
        print(f"❌ Error verifying tables: {e}")
        cursor.close()
        return []

def main():
    """Main execution function."""
    print("🧠 Brain Database Table Creation Script")
    print("=" * 50)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    sql_file_path = script_dir / 'create_brain_tables.sql'
    
    print(f"📁 SQL file path: {sql_file_path}")
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Read SQL file
        print("📖 Reading SQL commands...")
        sql_content = read_sql_file(sql_file_path)
        
        # Execute SQL commands
        print("🚀 Executing SQL commands...")
        successful_tables, failed_tables = execute_sql_commands(conn, sql_content)
        
        # Verify table creation
        print("\n🔍 Verifying table creation...")
        created_tables = verify_tables(conn)
        
        # Summary
        print(f"\n📈 Summary:")
        print(f"✅ Successfully created: {len(successful_tables)} tables")
        if failed_tables:
            print(f"❌ Failed statements: {len(failed_tables)}")
        
        print(f"\n🎉 Brain database setup complete!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()