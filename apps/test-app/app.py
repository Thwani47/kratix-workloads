from flask import Flask, jsonify, request
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'appdb'),
    'user': os.getenv('DB_USER', 'appuser'),
    'password': os.getenv('DB_PASSWORD', 'changeme')
}

def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    """Initialize the database schema."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(50)
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

# Initialize database on startup
init_db()

@app.route('/')
def home():
    """Home endpoint with visit tracking."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Record visit
        ip_address = request.remote_addr
        cur.execute('INSERT INTO visits (ip_address) VALUES (%s)', (ip_address,))
        conn.commit()

        # Get total visits
        cur.execute('SELECT COUNT(*) FROM visits')
        visit_count = cur.fetchone()[0]

        cur.close()
        conn.close()

        return jsonify({
            'message': 'Welcome to test-app!',
            'visits': visit_count,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'app': 'test-app',
        'version': '1.0.0'
    })

@app.route('/ready')
def ready():
    """Readiness check endpoint (includes database connectivity)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            'status': 'ready',
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'database': 'disconnected',
            'error': str(e)
        }), 503

@app.route('/api/visits')
def get_visits():
    """Get recent visits."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM visits ORDER BY timestamp DESC LIMIT 10')
        visits = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'visits': visits})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/info')
def info():
    """Application information."""
    return jsonify({
        'app_name': 'test-app',
        'version': '1.0.0',
        'environment': os.getenv('ENVIRONMENT', 'dev'),
        'database_host': DB_CONFIG['host']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
