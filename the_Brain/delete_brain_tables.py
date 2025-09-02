#!/usr/bin/env python3
"""
Brain Database Table Deletion Script

This script safely deletes all Brain-related tables from the database.
"""

import psycopg2
import sys

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

def delete_brain_tables(conn):
    """Delete all Brain-related tables."""
    cursor = conn.cursor()
    
    # List of all Brain tables to delete
    brain_tables = [
        'persons', 'organizations', 'places', 'events', 'conversations', 
        'tasks', 'projects', 'objects', 'media_documents', 'ideas', 
        'knowledge_facts', 'preferences', 'routines', 'health_episodes', 
        'travels', 'transactions', 'device_sessions', 'time_periods',
        'contexts', 'core_entities'  # Delete these last due to potential dependencies
    ]
    
    deleted_tables = []
    failed_deletions = []
    
    print("🗑️  Deleting Brain tables...")
    
    for table_name in brain_tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            conn.commit()
            deleted_tables.append(table_name)
            print(f"✅ Deleted table: {table_name}")
        except psycopg2.Error as e:
            conn.rollback()
            failed_deletions.append(table_name)
            print(f"❌ Error deleting table {table_name}: {e}")
    
    cursor.close()
    return deleted_tables, failed_deletions

def delete_brain_indexes(conn):
    """Delete all Brain-related indexes."""
    cursor = conn.cursor()
    
    brain_indexes = [
        'idx_core_entities_type', 'idx_core_entities_created_at', 
        'idx_core_entities_tags', 'idx_core_entities_salience',
        'idx_persons_relationship_strength', 'idx_events_event_type',
        'idx_tasks_status', 'idx_tasks_priority', 'idx_transactions_category',
        'idx_transactions_dt'
    ]
    
    deleted_indexes = []
    
    print("🗑️  Deleting Brain indexes...")
    
    for index_name in brain_indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
            conn.commit()
            deleted_indexes.append(index_name)
            print(f"✅ Deleted index: {index_name}")
        except psycopg2.Error as e:
            conn.rollback()
            print(f"❌ Error deleting index {index_name}: {e}")
    
    cursor.close()
    return deleted_indexes

def verify_deletion(conn):
    """Verify that Brain tables have been deleted."""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        remaining_tables = [row[0] for row in cursor.fetchall()]
        
        # Check if any Brain tables still exist
        brain_table_names = [
            'core_entities', 'contexts', 'persons', 'organizations', 'places', 
            'events', 'conversations', 'tasks', 'projects', 'objects', 
            'media_documents', 'ideas', 'knowledge_facts', 'preferences', 
            'routines', 'health_episodes', 'travels', 'transactions', 
            'device_sessions', 'time_periods'
        ]
        
        remaining_brain_tables = [table for table in remaining_tables if table in brain_table_names]
        
        print(f"\n📊 Deletion Verification:")
        print(f"Remaining tables in database: {len(remaining_tables)}")
        print(f"Remaining Brain tables: {len(remaining_brain_tables)}")
        
        if remaining_brain_tables:
            print(f"❌ These Brain tables still exist: {remaining_brain_tables}")
        else:
            print("✅ All Brain tables successfully deleted!")
        
        if remaining_tables:
            print(f"\n📋 Other tables still in database:")
            for table in remaining_tables:
                if table not in brain_table_names:
                    print(f"  • {table}")
        
        cursor.close()
        return len(remaining_brain_tables) == 0
        
    except psycopg2.Error as e:
        print(f"❌ Error verifying deletion: {e}")
        cursor.close()
        return False

def main():
    """Main execution function."""
    print("🗑️  Brain Database Table Deletion Script")
    print("=" * 50)
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        # Delete indexes first
        deleted_indexes = delete_brain_indexes(conn)
        
        # Delete tables
        deleted_tables, failed_deletions = delete_brain_tables(conn)
        
        # Verify deletion
        print("\n🔍 Verifying deletion...")
        success = verify_deletion(conn)
        
        # Summary
        print(f"\n📈 Summary:")
        print(f"✅ Deleted indexes: {len(deleted_indexes)}")
        print(f"✅ Deleted tables: {len(deleted_tables)}")
        if failed_deletions:
            print(f"❌ Failed deletions: {len(failed_deletions)}")
        
        if success:
            print(f"\n🎉 Brain tables cleanup complete!")
        else:
            print(f"\n⚠️  Some tables may not have been deleted completely.")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    main()