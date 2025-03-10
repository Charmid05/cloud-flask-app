from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "your_secret_key"

# Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Flask-Migrate for database migrations

# Define File Model
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    size = db.Column(db.Integer, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(50), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    files = File.query.all()
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    filename = request.form.get('filename')
    if not filename:
        flash('Please enter a filename', 'error')
        return redirect(url_for('index'))
    
    file_size = len(filename) * 1024  # Simulated file size
    file_type = filename.split('.')[-1] if '.' in filename else 'unknown'

    existing_file = File.query.filter_by(name=filename).first()
    if existing_file:
        flash(f'File {filename} already exists!', 'error')
        return redirect(url_for('index'))

    new_file = File(name=filename, size=file_size, type=file_type)
    db.session.add(new_file)
    db.session.commit()

    flash(f'File {filename} uploaded successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_file():
    file_id = request.form.get('file_id')
    new_name = request.form.get('new_name')
    
    if not file_id or not file_id.isdigit():
        flash('Invalid file ID', 'error')
        return redirect(url_for('index'))
    
    file = File.query.get(int(file_id))
    if not file:
        flash('File not found', 'error')
        return redirect(url_for('index'))
    
    if new_name:
        file.name = new_name
        file.type = new_name.split('.')[-1] if '.' in new_name else 'unknown'
        db.session.commit()
        flash(f'File renamed to {new_name}', 'success')
    else:
        flash('Please enter a new filename', 'error')
    
    return redirect(url_for('index'))

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    file = File.query.get(file_id)
    if file:
        db.session.delete(file)
        db.session.commit()
        flash(f'File {file.name} deleted successfully!', 'success')
    else:
        flash('File not found', 'error')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    files = File.query.filter(File.name.contains(query)).all()
    return jsonify([{'id': f.id, 'name': f.name, 'size': f.size, 'uploaded_at': f.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'), 'type': f.type} for f in files])

if __name__ == '__main__':
    app.run(debug=True)
