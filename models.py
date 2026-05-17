from extensions import db 
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# ==============================================================================
# (Table: users)
# ==============================================================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    avatar_url = db.Column(db.String(255), default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    time_created = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships:
    # 1. Novels published by this User
    novels = db.relationship('Novel', backref='author', lazy=True)
    # 2. Bookmarks made by this User
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)
    # 3. Comments made by this User
    comments = db.relationship('Comment', backref='user', lazy=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


# ==============================================================================
# (Table: novels)
# ==============================================================================
class Novel(db.Model):
    __tablename__ = 'novels'
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key link to the User table
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255), default='default_cover.png')
    genre = db.Column(db.String(50))
    status = db.Column(db.String(20), default='ongoing')
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    total_chapters = db.Column(db.Integer, default=0) 

    # Relationships:
    chapters = db.relationship('Chapter', backref='novel', cascade="all, delete-orphan", lazy='dynamic')
    bookmarks = db.relationship('Bookmark', backref='novel', lazy=True)

    def __repr__(self):
        return f"Novel('{self.title}', Author_ID: '{self.author_id}')"


# ==============================================================================
# (Table: chapters)
# ==============================================================================
class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to link the chapter back to its novel
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id'), nullable=False)
    
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False) 
    
    chapter_number = db.Column(db.Integer, nullable=False)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    last_updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.relationship('Comment', backref='chapter', lazy=True)
    
    def __repr__(self):
        return f"Chapter('{self.novel_id}', {self.chapter_number}: '{self.title}')"


# ==============================================================================
# (Table: bookmarks)
# ==============================================================================
class Bookmark(db.Model):
    __tablename__ = 'bookmarks'
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    novel_id = db.Column(db.Integer, db.ForeignKey('novels.id'), nullable=False)
    last_read_chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=True) 
    
    # Relationship
    last_read_chapter = db.relationship('Chapter', foreign_keys=[last_read_chapter_id])
    reading_status = db.Column(db.String(20), default='ongoing') 

    # Constraint to prevent duplicate
    __table_args__ = (db.UniqueConstraint('user_id', 'novel_id', name='_user_novel_uc'),)
    
    def __repr__(self):
        return f"Bookmark(User:{self.user_id}, Novel:{self.novel_id}, Chapter:{self.last_read_chapter_id})"


# ==============================================================================
# (Table: comments)
# ==============================================================================
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Comment('{self.content[:20]}...', Chapter:{self.chapter_id})"