# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory storage for Vercel deployment
# We'll initialize it from the file if it exists, but then use memory for operations
files_data = []

# File operations
def load_files():
    global files_data
    # If we have data in memory already, return it
    if files_data:
        return files_data
    
    # Otherwise try to load from file (for local development)
    STORAGE_FILE = 'files.json'
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r') as f:
                files_data = json.load(f)
                return files_data
        except Exception as e:
            print(f"Error loading file: {e}")
    
    # Default empty list if nothing exists
    return []

def save_files(files):
    global files_data
    # Update in-memory data
    files_data = files
    
    # For local development, also try to save to disk
    STORAGE_FILE = 'files.json'
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(files, f)
    except Exception as e:
        print(f"Error saving to file (expected in Vercel): {e}")
        # Continue anyway - this will work in memory even if file save fails

@app.route('/')
def index():
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
    
    files = load_files()
    # Check if file already exists
    if any(f['name'] == filename for f in files):
        flash(f'File {filename} already exists!', 'error')
        return redirect(url_for('index'))
    
    # Generate a new ID ensuring uniqueness
    new_id = 1
    if files:
        new_id = max(file['id'] for file in files) + 1
    
    # Add new file with metadata
    files.append({
        'id': new_id,
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
    files = load_files()
    
    if query:
        files = [f for f in files if query in f['name'].lower()]
    
    return jsonify(files)

if __name__ == '__main__':
    app.run(debug=True)