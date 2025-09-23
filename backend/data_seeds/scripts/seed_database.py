#!/usr/bin/env python3
"""
Script to seed the database with initial data.
Executes DDL first, then inserts data in a specific order to respect foreign key constraints.
"""

import os
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

# Import the table insertion order from config
from config import TABLES_INSERT_ORDER
from itapia_common.dblib.session import get_rdbms_session


def execute_sql_file(session: Session, file_path: str):
    """Execute a SQL file using the provided database session."""
    if not os.path.exists(file_path):
        print(f"Warning: File not found - {file_path}")
        return

    print(f"Executing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
        
    # Split the content into individual statements
    statements = sql_content.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                session.execute(text(statement))
                session.commit()
            except Exception as e:
                print(f"Error executing statement: {statement[:50]}...")
                print(f"Error: {e}")
                session.rollback()
                raise


def seed_database():
    """Main function to seed the database."""
    # Get database session
    rdbms_session = next(get_rdbms_session())
    
    try:
        # Get the data directory path
        script_dir = os.path.dirname(os.path.abspath(__file__, '..'))
        data_dir = os.path.join(script_dir, 'data')
        
        # First, execute the DDL file to create tables
        ddl_file = os.path.join(data_dir, 'ddl.sql')
        print("Executing DDL to create tables...")
        execute_sql_file(rdbms_session, ddl_file)
        
        # Then, execute the insert files in the specified order
        print("Inserting data in specified order...")
        for table_name in TABLES_INSERT_ORDER:
            # Map table names to their corresponding SQL files
            file_name = f'itapia_{table_name}'
            
            file_path = os.path.join(data_dir, file_name)
            execute_sql_file(rdbms_session, file_path)
        print("Database seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during database seeding: {e}")
        raise
    finally:
        rdbms_session.close()


if __name__ == "__main__":
    seed_database()