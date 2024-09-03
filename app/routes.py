import os
import shutil
from flask import jsonify, render_template, url_for, flash, redirect, request, abort, send_from_directory, current_app as app
from wtforms import ValidationError
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, FolderForm, UploadForm
from app.models import User, Folder, File
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from datetime import datetime


@app.route("/", methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], form.username.data)
        os.makedirs(user_folder, exist_ok=True)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, root_folder=user_folder)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

from sqlalchemy import func

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    form = FolderForm()

    # Handle folder creation
    if form.validate_on_submit():
        folder_name = form.name.data.strip()  # Remove leading and trailing spaces from the folder name
        folder_path = os.path.join(current_user.root_folder, folder_name)

        # Check if a folder with the same name already exists at the top level
        duplicate_folder = Folder.query.filter_by(name=folder_name, user_id=current_user.id, parent_id=None).first()
        if duplicate_folder:
            flash('A folder with this name already exists. Please choose a different name.', 'info')
            return redirect(url_for('home'))

        os.makedirs(folder_path, exist_ok=True)
        folder = Folder(name=folder_name, user_id=current_user.id, path=folder_path, parent_id=None)
        db.session.add(folder)
        db.session.commit()
        flash('Folder created successfully!', 'success')
        return redirect(url_for('home'))
    
    # Query top-level folders
    top_level_folders = Folder.query.filter_by(user_id=current_user.id, parent_id=None).all()

    # Prepare the list of folder details
    folders = []
    for folder in top_level_folders:
        subfolder_count = Folder.query.filter_by(parent_id=folder.id).count()
        file_count = File.query.filter_by(folder_id=folder.id).count()
        folders.append({
            'folder': folder,
            'subfolder_count': subfolder_count,
            'file_count': file_count
        })

    # Calculate total subfolders and files for all levels
    total_subfolders = Folder.query.filter(Folder.user_id == current_user.id).count()
    total_files = File.query.join(Folder).filter(Folder.user_id == current_user.id).count()

    return render_template('home.html', title='Home', folders=folders, total_subfolders=total_subfolders, total_files=total_files, form=form)


@app.route("/<username>/folder/<int:folder_id>", methods=['GET', 'POST'])
@login_required
def folder(username, folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id or current_user.username != username:
        abort(403)
    
    # Handle creating new subfolders
    form = FolderForm()
    upload_form = UploadForm()
    
    if form.validate_on_submit():
        folder_name = form.name.data.strip()  # Remove leading and trailing spaces from folder name
        folder_path = os.path.join(folder.path, folder_name)

        # Check if a folder with the same name already exists within the current folder
        duplicate_folder = Folder.query.filter_by(name=folder_name, parent_id=folder.id).first()
        if duplicate_folder:
            flash('A folder with this name already exists. Please choose a different name.', 'info')
            return redirect(url_for('folder', username=username, folder_id=folder.id))
        
        os.makedirs(folder_path, exist_ok=True)
        new_folder = Folder(name=folder_name, user_id=current_user.id, path=folder_path, parent_id=folder.id)
        db.session.add(new_folder)
        db.session.commit()
        flash('Folder created successfully!', 'success')
        return redirect(url_for('folder', username=username, folder_id=folder.id))
    if upload_form.validate_on_submit():
            file = upload_form.file.data
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1]
            new_filename = f"{upload_form.new_name.data.strip()}{file_extension}"
            file_path = os.path.join(folder.path, new_filename)
    
            existing_file = File.query.filter_by(name=new_filename, folder_id=folder.id).first()
            if existing_file:
                flash('A file with this name already exists. Please choose a different name.', 'info')
                return jsonify({'flash': {'category': 'info', 'message': 'A file with this name already exists. Please choose a different name.'}})
    
            file.save(file_path)
            relative_path = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
            new_file = File(name=new_filename, folder_id=folder.id, path=relative_path)
            db.session.add(new_file)
            db.session.commit()
            flash('File uploaded successfully!', 'success')
            return jsonify({'redirect': url_for('folder', username=username, folder_id=folder.id)})
    
    if upload_form.file.errors:
            flash(f"Upload failed: {upload_form.file.errors[0]}", 'danger')
            return jsonify({'flash': {'category': 'danger', 'message': 'Upload failed: ' + upload_form.file.errors[0]}})
    
    # Fetch subfolders and files
    subfolders = Folder.query.filter_by(parent_id=folder.id).all()
    files = File.query.filter_by(folder_id=folder.id).all()

    # Provide a link to go up to the parent folder
    parent_folder = Folder.query.get(folder.parent_id) if folder.parent_id else None

    return render_template('folder.html', title=folder.name, folder=folder, subfolders=subfolders, files=files, form=form, upload_form=upload_form, parent_folder=parent_folder)

@app.route("/search", methods=['GET'])
@login_required
def search():
    query = request.args.get('query')
    if query:
        # Filter files by checking the folder's user_id
        files = db.session.query(File).join(Folder).filter(
            File.name.ilike(f'%{query}%'),
            Folder.user_id == current_user.id
        ).all()
    else:
        files = []

    return render_template('search_results.html', title='Search Results', files=files, query=query)


@app.route("/uploads/<path:filename>")
@login_required
def download_file(filename):
    directory = app.config['UPLOAD_FOLDER']
    file_path = os.path.join(directory, filename)
    
    print(f"Directory: {directory}")
    print(f"Requested file: {filename}")
    print(f"Full file path: {file_path}")
    print(f"File exists: {os.path.isfile(file_path)}")

    if not os.path.isfile(file_path):
        abort(404)  # File not found
    return send_from_directory(directory, filename)

@app.route("/delete_folder/<int:folder_id>", methods=['POST'])
@login_required
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        abort(403)

    # Delete subfolders and files within this folder
    for subfolder in Folder.query.filter_by(parent_id=folder.id).all():
        delete_folder(subfolder.id)
    
    for file in File.query.filter_by(folder_id=folder.id).all():
        delete_file(file.id)
    
    # Delete the folder from the filesystem
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder.path)
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    
    # Remove folder record from database
    db.session.delete(folder)
    db.session.commit()
    flash('Folder has been deleted!', 'success')
    
    # Redirect back to the parent folder or home if no parent
    parent_folder = Folder.query.get(folder.parent_id)
    if parent_folder:
        return redirect(url_for('folder', username=current_user.username, folder_id=parent_folder.id))
    else:
        return redirect(url_for('home'))

@app.route("/delete_file/<int:file_id>", methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.folder.user_id != current_user.id:
        abort(403)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.path)
    if os.path.isfile(file_path):
        os.remove(file_path)
    
    db.session.delete(file)
    db.session.commit()
    flash('File has been deleted!', 'success')
    return redirect(url_for('folder', username=current_user.username, folder_id=file.folder_id))

