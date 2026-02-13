"""
Pulse Backend - Entry Point

Run this file to start the Flask development server.

Usage:
    python run.py
"""

import os
from app import create_app

# Get environment from .env file (defaults to development)
config_name = os.getenv('FLASK_ENV', 'development')

# Create Flask app
app = create_app(config_name)

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ╔═══════════════════════════════════════╗
    ║     PULSE BACKEND - STARTING UP       ║
    ╚═══════════════════════════════════════╝
    
    Environment: {config_name}
    Host: {host}
    Port: {port}
    Debug: {debug}
    
    API will be available at: http://{host}:{port}
    
    Press CTRL+C to stop the server
    """)
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )
