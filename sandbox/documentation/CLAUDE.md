# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **B2 Brain Database System** - a comprehensive PostgreSQL-based knowledge management system for personal information storage and retrieval. The system is designed as a "second brain" with both relational and vector database integration capabilities.

## Architecture

### Core Design
- **19 entity tables** with universal core convention fields plus category-specific attributes
- **PostgreSQL backend** with JSONB for flexible data modeling
- **Vector integration ready** via `embedding_refs` fields
- **Flexible relationships** through JSONB `links` fields
- **Centralized contexts** table for reusable situational information

### Entity Categories
The system manages 19 entity types: persons, organizations, places, events, conversations, tasks, projects, objects, media_documents, ideas, knowledge_facts, preferences, routines, health_episodes, travels, transactions, device_sessions, time_periods, and a support table for contexts.

All entity tables share identical core convention fields (40+ fields including id, type, title, aliases, summary, embedding_refs, time_info, location_info, context_id, tags, salience, emotion, confidence, source_info, provenance, privacy_info, links, access_info, timestamps) plus category-specific extensions.

## Database Connection

**Connection Details:**
- Host: localhost:9876
- Database: general2613  
- User: kadmin
- Password: securepasswordkossher123

**Connection String:**
```
postgresql://kadmin:securepasswordkossher123@localhost:9876/general2613
```

**Direct psql Access:**
```bash
PGPASSWORD=securepasswordkossher123 psql -h localhost -p 9876 -U kadmin -d general2613
```

## Development Commands

### Primary Tool: sql_runner.py
The main development tool is `sql_runner.py` - a flexible PostgreSQL execution utility with configuration management.

**Basic Usage:**
```bash
# Execute SQL file with default config
python sql_runner.py create_brain_tables_corrected.sql

# Use custom configuration  
python sql_runner.py --config custom_config.json schema.sql

# Delete tables from list
python sql_runner.py --delete-tables brain_tables_list.txt

# Verify tables exist
python sql_runner.py --verify --expected-tables persons,events,tasks

# Combined operations
python sql_runner.py create_brain_tables_corrected.sql --verify
```



### Table Management
```bash
# Drop all Brain tables
python sql_runner.py --delete-tables brain_tables_list.txt

# Recreate all tables
python sql_runner.py --delete-tables brain_tables_list.txt
python sql_runner.py create_brain_tables_corrected.sql --verify

# Legacy scripts (use sql_runner.py instead)
python create_brain_tables.py
python delete_brain_tables.py  
python recreate_brain_tables.py
```

## Key Files

### SQL Schema
- `create_brain_tables_corrected.sql` - **Current/correct schema** (use this)
- `create_brain_tables.sql` - Original (incorrect) schema
- `brain_tables_list.txt` - Ordered list of all Brain tables for management

### Configuration
- `config.json` - Database connection and execution settings
- `the_Brain/README.md` - Comprehensive system documentation

documentation is a key here. After finishing every single round of responses and before letting me giving the next input, write down what has been done and how to use the development results. Besides, we need to have plantuml diagram for the entire kingdom system from the beginning to the end for all the agents and sub-agents. Make the already    working agents green, make to-do tasks black, and make further  development orange. Make helper and other tools blue.   

### Python Tools
- `sql_runner.py` - **Primary development tool** - flexible SQL execution
- `create_brain_tables.py` - Legacy table creation script
- `delete_brain_tables.py` - Legacy table deletion script  
- `recreate_brain_tables.py` - Legacy full recreation script

## Configuration Management

The system uses `config.json` for centralized settings:
- Database connection parameters
- Execution settings (auto_commit, verbose, stop_on_error, show_progress)
- File paths (sql_files_dir, logs_dir)

## Common Database Operations

### Table Verification
```sql
-- View all tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' ORDER BY table_name;

-- Check table structure  
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'persons' ORDER BY ordinal_position;

-- Table row counts
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables WHERE schemaname = 'public'
ORDER BY tablename;
```

## Development Workflow

1. **Schema Changes:** Modify `create_brain_tables_corrected.sql`
2. **Apply Changes:** Use `sql_runner.py` to execute SQL
3. **Verify:** Use `--verify` flag to confirm table creation
4. **Table Management:** Use `brain_tables_list.txt` for bulk operations

## Important Notes

- Always use `create_brain_tables_corrected.sql` (not the original version)
- Use `sql_runner.py` as the primary tool (more flexible than legacy scripts)
- The system is designed for PostgreSQL with JSONB support
- All tables follow the same core convention field structure
- Vector database integration is supported via `embedding_refs` fields