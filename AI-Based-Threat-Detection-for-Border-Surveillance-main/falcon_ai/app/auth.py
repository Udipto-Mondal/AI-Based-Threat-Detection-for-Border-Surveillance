from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime
from . import mongo, bcrypt
from bson import ObjectId

bp = Blueprint('auth', __name__)

class User(UserMixin):
    """User model for MongoDB with Flask-Login integration"""
    
    def __init__(self, username, email, password_hash, role='user', _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self._id = _id
    
    @property
    def id(self):
        """Return ID as string"""
        return str(self._id) if self._id else None

    def get_id(self):
        """Required by Flask-Login"""
        return str(self._id) if self._id else None
    
    @staticmethod
    def get_by_id(user_id):
        """Load user by ID from MongoDB"""
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    role=user_data.get('role', 'user'),
                    _id=user_data['_id']
                )
        except Exception as e:
            print(f"Error loading user: {e}")
        return None
    
    @staticmethod
    def get_by_username(username):
        """Load user by username from MongoDB"""
        try:
            user_data = mongo.db.users.find_one({'username': username})
            if user_data:
                return User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    role=user_data.get('role', 'user'),
                    _id=user_data['_id']
                )
        except Exception as e:
            print(f"Error loading user: {e}")
        return None
    
    def save(self):
        """Save user to MongoDB"""
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role,
            'created_at': datetime.utcnow()
        }
        if self._id:
            mongo.db.users.update_one({'_id': self._id}, {'$set': user_data})
        else:
            result = mongo.db.users.insert_one(user_data)
            self._id = result.inserted_id
        return self


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        
        try:
            # Check if user exists
            if mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]}):
                flash('Username or email already exists.', 'error')
                return render_template('register.html')
            
            # Create new user
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(username=username, email=email, password_hash=password_hash)
            user.save()
            
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f'\u274c Registration DB error: {e}')
            flash(f'Database connection error. Please check MONGO_URI configuration. Details: {e}', 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        try:
            user = User.get_by_username(username)
            
            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user, remember=True)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            print(f'\u274c Login DB error: {e}')
            flash(f'Database connection error. Details: {e}', 'error')
    
    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

