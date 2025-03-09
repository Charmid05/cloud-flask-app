# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# For loading environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'your_secret_key'

# Simulated storage - fallback for local development
STORAGE_FILE = 'files.json'
USE_DATABASE = True  # Default to database, will switch to False if connection fails

def load_files():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_files(files):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(files, f)

# Database connection
def get_db_connection():
    global USE_DATABASE  # Declare global before using it
    
    # Get database URL from environment variable
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not DATABASE_URL:
        USE_DATABASE = False
        print("Warning: DATABASE_URL not set. Using fallback JSON storage.")
        return None
    
    try:
        # Add SSL requirements for Render
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode='require'
        )
        return conn
    except Exception as e:
        USE_DATABASE = False
        print(f"Database connection error: {e}")
        print("Falling back to JSON storage.")
        return None

# Initialize the database
def init_db():
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cur = conn.cursor()
        # Create files table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                size INTEGER NOT NULL,
                uploaded_at TIMESTAMP NOT NULL,
                type VARCHAR(50) NOT NULL
            );
        ''')
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Initialize on startup
try:
    with app.app_context():
        db_init_success = init_db()
        if db_init_success:
            print("Database initialized successfully")
        else:
            print("Using JSON file storage instead")
except Exception as e:
    USE_DATABASE = False
    print(f"Error during initialization: {e}")
    print("Using JSON file storage instead")

@app.route('/')
def index():
    if USE_DATABASE:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                cur.execute('SELECT * FROM files ORDER BY uploaded_at DESC;')
                files = cur.fetchall()
                cur.close()
                conn.close()
                return render_template('index.html', files=files)
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback to JSON
    files = load_files()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    filename = request.form.get('filename')
    if not filename:
        flash('Please enter a filename', 'error')
        return redirect(url_for('index'))
    
    # Simulate file size calculation
    file_size = len(filename) * 1024  # Fake size in KB
    
    if USE_DATABASE:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                # Check if file already exists
                cur.execute('SELECT COUNT(*) FROM files WHERE name = %s;', (filename,))
                if cur.fetchone()[0] > 0:
                    cur.close()
                    conn.close()
                    flash(f'File {filename} already exists!', 'error')
                    return redirect(url_for('index'))
                
                # Add new file with metadata
                cur.execute('''
                    INSERT INTO files (name, size, uploaded_at, type)
                    VALUES (%s, %s, %s, %s);
                ''', (
                    filename, 
                    file_size, 
                    datetime.now(), 
                    filename.split('.')[-1] if '.' in filename else 'unknown'
                ))
                
                conn.commit()
                cur.close()
                conn.close()
                flash(f'File {filename} uploaded successfully!', 'success')
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback to JSON
    files = load_files()
    # Check if file already exists
    if any(f['name'] == filename for f in files):
        flash(f'File {filename} already exists!', 'error')
        return redirect(url_for('index'))
    
    # Add new file with metadata
    files.append({
        'id': len(files) + 1,
        'name': filename,
        'size': file_size,
        'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'type': filename.split('.')[-1] if '.' in filename else 'unknown'
    })
    
    save_files(files)
    flash(f'File {filename} uploaded successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_file():
    file_id = int(request.form.get('file_id'))
    new_name = request.form.get('new_name')
    
    if not new_name:
        flash('Please enter a new filename', 'error')
        return redirect(url_for('index'))
    
    if USE_DATABASE:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                
                # Get old name for the flash message
                cur.execute('SELECT name FROM files WHERE id = %s;', (file_id,))
                result = cur.fetchone()
                
                if result:
                    old_name = result[0]
                    # Update the file
                    cur.execute('''
                        UPDATE files 
                        SET name = %s, type = %s 
                        WHERE id = %s;
                    ''', (
                        new_name, 
                        new_name.split('.')[-1] if '.' in new_name else 'unknown',
                        file_id
                    ))
                    conn.commit()
                    flash(f'File renamed from {old_name} to {new_name}', 'success')
                else:
                    flash('File not found', 'error')
                
                cur.close()
                conn.close()
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback to JSON
    files = load_files()
    
    # Check if file exists
    for file in files:
        if file['id'] == file_id:
            old_name = file['name']
            file['name'] = new_name
            file['type'] = new_name.split('.')[-1] if '.' in new_name else 'unknown'
            save_files(files)
            flash(f'File renamed from {old_name} to {new_name}', 'success')
            break
    else:
        flash('File not found', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    if USE_DATABASE:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                
                # Get file name for the flash message
                cur.execute('SELECT name FROM files WHERE id = %s;', (file_id,))
                result = cur.fetchone()
                
                if result:
                    deleted_file_name = result[0]
                    # Delete the file
                    cur.execute('DELETE FROM files WHERE id = %s;', (file_id,))
                    conn.commit()
                    flash(f'File {deleted_file_name} deleted successfully!', 'success')
                else:
                    flash('File not found', 'error')
                
                cur.close()
                conn.close()
                return redirect(url_for('index'))
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback to JSON
    files = load_files()
    
    # Find and remove the file
    for i, file in enumerate(files):
        if file['id'] == file_id:
            deleted_file = files.pop(i)
            save_files(files)
            flash(f'File {deleted_file["name"]} deleted successfully!', 'success')
            break
    else:
        flash('File not found', 'error')
    
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    
    if USE_DATABASE:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                if query:
                    cur.execute("SELECT * FROM files WHERE LOWER(name) LIKE %s;", (f'%{query}%',))
                else:
                    cur.execute("SELECT * FROM files;")
                
                files = cur.fetchall()
                cur.close()
                conn.close()
                return jsonify(files)
        except Exception as e:
            print(f"Database error: {e}")
    
    # Fallback to JSON
    files = load_files()
    
    if query:
        files = [f for f in files if query in f['name'].lower()]
    
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True)

# # app.py
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# import os
# import json
# from datetime import datetime



# # app = Flask(__name__)
# app = Flask(__name__, static_folder="static", template_folder="templates")
# app.secret_key = 'your_secret_key'

# # Simulated storage - in a real app, this would be a database
# STORAGE_FILE = 'files.json'

# def load_files():
#     if os.path.exists(STORAGE_FILE):
#         with open(STORAGE_FILE, 'r') as f:
#             return json.load(f)
#     return []

# def save_files(files):
#     with open(STORAGE_FILE, 'w') as f:
#         json.dump(files, f)

# @app.route('/')
# def index():
#     files = load_files()
#     return render_template('index.html', files=files)

# @app.route('/upload', methods=['POST'])
# def upload_file():
#     filename = request.form.get('filename')
#     if not filename:
#         flash('Please enter a filename', 'error')
#         return redirect(url_for('index'))
    
#     # Simulate file size calculation
#     file_size = len(filename) * 1024  # Fake size in KB
    
#     files = load_files()
#     # Check if file already exists
#     if any(f['name'] == filename for f in files):
#         flash(f'File {filename} already exists!', 'error')
#         return redirect(url_for('index'))
    
#     # Add new file with metadata
#     files.append({
#         'id': len(files) + 1,
#         'name': filename,
#         'size': file_size,
#         'uploaded_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         'type': filename.split('.')[-1] if '.' in filename else 'unknown'
#     })
    
#     save_files(files)
#     flash(f'File {filename} uploaded successfully!', 'success')
#     return redirect(url_for('index'))

# @app.route('/update', methods=['POST'])
# def update_file():
#     file_id = int(request.form.get('file_id'))
#     new_name = request.form.get('new_name')
    
#     if not new_name:
#         flash('Please enter a new filename', 'error')
#         return redirect(url_for('index'))
    
#     files = load_files()
    
#     # Check if file exists
#     for file in files:
#         if file['id'] == file_id:
#             old_name = file['name']
#             file['name'] = new_name
#             file['type'] = new_name.split('.')[-1] if '.' in new_name else 'unknown'
#             save_files(files)
#             flash(f'File renamed from {old_name} to {new_name}', 'success')
#             break
#     else:
#         flash('File not found', 'error')
    
#     return redirect(url_for('index'))

# @app.route('/delete/<int:file_id>', methods=['POST'])
# def delete_file(file_id):
#     files = load_files()
    
#     # Find and remove the file
#     for i, file in enumerate(files):
#         if file['id'] == file_id:
#             deleted_file = files.pop(i)
#             save_files(files)
#             flash(f'File {deleted_file["name"]} deleted successfully!', 'success')
#             break
#     else:
#         flash('File not found', 'error')
    
#     return redirect(url_for('index'))

# @app.route('/search')
# def search():
#     query = request.args.get('query', '').lower()
#     files = load_files()
    
#     if query:
#         files = [f for f in files if query in f['name'].lower()]
    
#     return jsonify(files)

# if __name__ == '__main__':
#     app.run(debug=True)