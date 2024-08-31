import os
from flask import render_template, url_for, flash, redirect, request, abort, send_from_directory
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
        flash(f'Your account has been created! You are now able to log in', 'success')
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

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    form = FolderForm()
    if form.validate_on_submit():
        folder_path = os.path.join(current_user.root_folder, form.name.data)
        os.makedirs(folder_path, exist_ok=True)
        folder = Folder(name=form.name.data, user_id=current_user.id, path=folder_path, parent_id=None)
        db.session.add(folder)
        db.session.commit()
        return redirect(url_for('home'))
    
    folders = Folder.query.filter_by(user_id=current_user.id, parent_id=None).all()
    files = File.query.join(Folder).filter(Folder.user_id == current_user.id, Folder.parent_id == None).all()
    
    return render_template('home.html', title='Home', folders=folders, files=files, form=form)

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
        folder_path = os.path.join(folder.path, form.name.data)
        os.makedirs(folder_path, exist_ok=True)
        new_folder = Folder(name=form.name.data, user_id=current_user.id, path=folder_path, parent_id=folder.id)
        db.session.add(new_folder)
        db.session.commit()
        return redirect(url_for('folder', username=username, folder_id=folder.id))
    
    # Handle file uploads
    if upload_form.validate_on_submit():
        file = upload_form.file.data
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]  # Extract the original file extension
        new_filename = f"{upload_form.new_name.data}{file_extension}"  # Combine new name with original extension
        file_path = os.path.join(folder.path, new_filename)
        file.save(file_path)
        new_file = File(name=new_filename, folder_id=folder.id, path=file_path)
        db.session.add(new_file)
        db.session.commit()
        return redirect(url_for('folder', username=username, folder_id=folder.id))
    
    # Fetch subfolders and files
    subfolders = Folder.query.filter_by(parent_id=folder.id).all()
    files = File.query.filter_by(folder_id=folder.id).all()

    # Provide a link to go up to the parent folder
    parent_folder = Folder.query.get(folder.parent_id) if folder.parent_id else None

    return render_template('folder.html', title=folder.name, folder=folder, subfolders=subfolders, files=files, form=form, upload_form=upload_form, parent_folder=parent_folder)

@app.route("/uploads/<path:filename>")
@login_required
def download_file(filename):
    directory = app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename)
