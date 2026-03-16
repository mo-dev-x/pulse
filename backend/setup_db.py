#!/usr/bin/env python3
"""
Database Setup Script for Pulse Backend

This script helps you:
1. Create the MySQL database
2. Execute the schema.sql file
3. Verify the setup

Usage:
    python setup_db.py
"""

import pymysql
import os
import sys
from getpass import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """
    Non-interactive DB setup for cloud deployment
    """
    creds = {
        'host': os.getenv('MYSQLHOST'),
        'port': int(os.getenv('MYSQLPORT', 3306)),
        'user': os.getenv('MYSQLUSER'),
        'password': os.getenv('MYSQLPASSWORD'),
        'db_name': os.getenv('MYSQLDATABASE')
    }

    connection = pymysql.connect(
        host=creds['host'],
        port=creds['port'],
        user=creds['user'],
        password=creds['password'],
        database=creds['db_name']
    )

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    if tables:
        print("✅ Tables already exist → skipping schema setup")
        return

    print("🚀 First deployment → creating schema")
    execute_schema(creds)

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")


def get_db_credentials():
    """
    Get database credentials from user or .env file
    """
    print_header("DATABASE CREDENTIALS")
    
    # Try to get from .env first
    host = os.getenv('MYSQLHOST')
    port = int(os.getenv('MYSQLPORT', 3306))
    user = os.getenv('MYSQLUSER')
    password = os.getenv('MYSQLPASSWORD')
    db_name = os.getenv('MYSQLDATABASE')
    
    # If not in .env, ask user
    if not user:
        print("Enter MySQL credentials (or set them in .env file)")
        user = input(f"MySQL Username [{os.getenv('USER', 'root')}]: ").strip() or os.getenv('USER', 'root')
    
    if not password:
        password = getpass("MySQL Password: ")
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'db_name': db_name
    }


def test_connection(creds):
    """
    Test MySQL connection without selecting database
    """
    print_header("TESTING CONNECTION")
    
    try:
        connection = pymysql.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            charset='utf8mb4'
        )
        print(f"✅ Successfully connected to MySQL at {creds['host']}:{creds['port']}")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def create_database(creds):
    """
    Create the pulse_db database if it doesn't exist
    """
    print_header("CREATING DATABASE")
    
    try:
        connection = pymysql.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {creds['db_name']} "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        
        print(f"✅ Database '{creds['db_name']}' created (or already exists)")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def execute_schema(creds):
    """
    Execute the schema.sql file
    """
    print_header("EXECUTING SCHEMA")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    schema_file = os.path.join(BASE_DIR, 'schema.sql')
    
    if not os.path.exists(schema_file):
        print(f"❌ Schema file '{schema_file}' not found")
        return False
    
    try:
        # Read schema file
        with open(schema_file, 'r', encoding='utf8') as f:
            schema_sql = f.read()
        
        # Connect to database
        connection = pymysql.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            database=creds['db_name'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Split and execute SQL statements
        # Remove comments and split by semicolon
        statements = []
        current_statement = []
        
        for line in schema_sql.split('\n'):
            # Skip comments
            if line.strip().startswith('--') or line.strip().startswith('/*'):
                continue
            
            current_statement.append(line)
            
            # If line ends with semicolon, it's a complete statement
            if line.strip().endswith(';'):
                statement = '\n'.join(current_statement).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current_statement = []
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # Some statements might fail if they already exist (views, procedures)
                    # We'll continue anyway
                    if 'already exists' not in str(e).lower():
                        print(f"⚠️  Warning: {e}")
        
        connection.commit()
        print(f"✅ Schema executed successfully ({len(statements)} statements)")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to execute schema: {e}")
        return False


def verify_setup(creds):
    """
    Verify that tables were created correctly
    """
    print_header("VERIFYING SETUP")
    
    try:
        connection = pymysql.connect(
            host=creds['host'],
            port=creds['port'],
            user=creds['user'],
            password=creds['password'],
            database=creds['db_name'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'users', 'followers', 'campus_zones', 'posts', 
            'media', 'reactions', 'daily_aggregates', 
            'weekly_aggregates', 'events'
        ]
        
        print("Tables created:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (MISSING)")
        
        # Check campus zones
        cursor.execute("SELECT COUNT(*) FROM campus_zones")
        zone_count = cursor.fetchone()[0]
        print(f"\nCampus zones seeded: {zone_count} zones")
        
        if zone_count > 0:
            cursor.execute("SELECT name FROM campus_zones LIMIT 5")
            zones = cursor.fetchall()
            print("Sample zones:")
            for zone in zones:
                print(f"  - {zone[0]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def update_env_file(creds):
    """
    Offer to update .env file with database credentials
    """
    print_header("UPDATE .ENV FILE")
    
    env_file = '.env'
    
    if os.path.exists(env_file):
        response = input("Update .env file with these credentials? (y/n): ").lower()
        if response != 'y':
            print("Skipped .env update")
            return
    
    # Read template or create new
    env_template = '.env.template'
    if os.path.exists(env_template):
        with open(env_template, 'r') as f:
            env_content = f.read()
    else:
        env_content = ""
    
    # Update database values
    env_lines = []
    for line in env_content.split('\n'):
        if line.startswith('DB_HOST='):
            env_lines.append(f"DB_HOST={creds['host']}")
        elif line.startswith('DB_PORT='):
            env_lines.append(f"DB_PORT={creds['port']}")
        elif line.startswith('DB_NAME='):
            env_lines.append(f"DB_NAME={creds['db_name']}")
        elif line.startswith('DB_USER='):
            env_lines.append(f"DB_USER={creds['user']}")
        elif line.startswith('DB_PASSWORD='):
            env_lines.append(f"DB_PASSWORD={creds['password']}")
        else:
            env_lines.append(line)
    
    # Write to .env
    with open(env_file, 'w') as f:
        f.write('\n'.join(env_lines))
    
    print(f"✅ Updated {env_file}")


def main():
    """
    Main setup flow
    """
    print("""
    ╔═══════════════════════════════════════╗
    ║   PULSE DATABASE SETUP WIZARD         ║
    ╚═══════════════════════════════════════╝
    
    This script will:
    1. Test MySQL connection
    2. Create pulse_db database
    3. Execute schema (create tables)
    4. Seed initial data
    5. Verify setup
    """)
    
    # Get credentials
    creds = get_db_credentials()
    
    # Test connection
    if not test_connection(creds):
        print("\n❌ Setup failed: Could not connect to MySQL")
        print("Please check your credentials and MySQL server status")
        sys.exit(1)
    
    # Create database
    if not create_database(creds):
        print("\n❌ Setup failed: Could not create database")
        sys.exit(1)
    
    # Execute schema
    if not execute_schema(creds):
        print("\n❌ Setup failed: Could not execute schema")
        sys.exit(1)
    
    # Verify setup
    if not verify_setup(creds):
        print("\n⚠️  Setup completed with warnings")
    else:
        print("\n✅ Setup completed successfully!")
    
    # Update .env
    update_env_file(creds)
    
    print("""
    ╔═══════════════════════════════════════╗
    ║   NEXT STEPS                          ║
    ╚═══════════════════════════════════════╝
    
    1. Generate secret keys:
       python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
       python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
    
    2. Add these to your .env file
    
    3. Test the app:
       python run.py
    
    4. Verify API is running:
       curl http://127.0.0.1:5000/
    """)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
