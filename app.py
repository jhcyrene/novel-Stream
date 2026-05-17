from flask import Flask, render_template, current_app
from extensions import db
from models import User, Novel, Chapter, Bookmark
from datetime import datetime
from werkzeug.security import generate_password_hash
import random

# Import Blueprints
from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp

def create_app():
    # ------ App Setup ------
    app = Flask(__name__)
    app.secret_key = 'deaNovelStreamMeow'

    # Configure Database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///storystream.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors.html', 
                               error_title="Page Not Found", 
                               error_message="The page you are looking for doesn't exist."), 404

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def internal_server_error(e):
        print(f"--- SERVER ERROR LOGGED ---\n{e}\n---------------------------") 
        
        return render_template('errors.html', 
                               error_title="Server Error", 
                               error_message="We encountered a technical glitch. Our team has been notified."), 500

    return app

# --- Database Initialization ---
def create_admin():
    print("--- Checking Administrator Status ---")
    default_email = "admin@admin.com"

    user = User.query.filter_by(email=default_email).first()

    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User '{user.username}' verified as admin.")
    else:
        try:
            new_admin = User(
                username="AdminUser",
                email=default_email,
                password_hash=generate_password_hash("AdminPass123"), 
                is_admin=True
            )
            db.session.add(new_admin)

            new_user = User(
                username="User",
                email="user@user.com",
                password_hash=generate_password_hash("user12345678"), 
                is_admin=False
            )
            db.session.add(new_user)

            db.session.commit()
            print("Administrator account created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to create admin: {e}")

def create_sample_data():
    if Novel.query.count() > 0:
        return

    print("--- Generating Large Batch of Sample Data ---")

    # 1. Create the Author
    author = User(
        username='StoryMaster',
        email='author@example.com',
        password_hash=generate_password_hash('password123'),
        is_admin=False
    )
    db.session.add(author)
    db.session.commit()

    genres = ['Fantasy', 'Sci-Fi', 'Romance', 'Mystery', 'Horror', 'Thriller', 'Cultivation']
    statuses = ['ongoing', 'completed', 'hiatus']
    adjectives = ['Eternal', 'Shadow', 'Golden', 'Lost', 'Forgotten', 'Silent', 'Crimson']
    nouns = ['Kingdom', 'Void', 'Prophecy', 'Legacy', 'Crest', 'Empire', 'Soul']
    paragraphs = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec id erat placerat nunc aliquam convallis ac vel eros. Nam efficitur volutpat odio a commodo. Maecenas non felis id purus sodales viverra.",
        "Phasellus et dolor mollis, gravida lectus id, ultrices ligula. Cras quis ligula elementum, maximus velit non, varius nunc. Nullam vel quam dapibus, consequat massa non, ornare magna.",
        "Proin pulvinar faucibus sodales. Aliquam aliquet eleifend odio, eget mattis est tincidunt egestas. Morbi euismod pretium varius. Proin sit amet efficitur nisi, et convallis nulla.",
        "Sed cursus eros ut dui porttitor, sit amet tempor tellus maximus. Nullam eget commodo nunc. Nam et nisl nec velit vestibulum accumsan. Pellentesque laoreet pellentesque rhoncus.",
        "Aliquam erat volutpat. Curabitur semper leo in nulla interdum varius. Integer aliquam ante tristique molestie porttitor. Aenean vitae commodo mi. In malesuada lorem sed libero faucibus lobortis."
    ]

    # Start Generating Novels
    for i in range(1, 61):
        title = f"{random.choice(adjectives)} {random.choice(nouns)} #{i}"
        
        new_novel = Novel(
            author_id=author.id,
            title=title,
            description=f"An epic tale about the {title}. Explore a world of {random.choice(genres).lower()} and adventure.",
            genre=random.choice(genres),
            status=random.choice(statuses),
        )
        db.session.add(new_novel)
        db.session.flush()

        # 2. Add Chapters in the novel
        for c_num in range(1, 101):
            selected_content = random.choices(paragraphs, k=random.randint(10, 15))
            html_content = "".join([f"<p>{p}</p>" for p in selected_content])

            new_chapter = Chapter(
                novel_id=new_novel.id,
                chapter_number=c_num,
                title=f"The Beginning of the End - Part {c_num}",
                content=html_content,
                is_published=True,
                published_at=datetime.utcnow()
            )
            db.session.add(new_chapter)

        db.session.commit() 
        print(f"Created Novel {i}/100: '{title}' with 500 chapters...")

    print("--- 100 Novels and 50,000 Chapters Inserted Successfully! ---")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
        create_admin()
        create_sample_data()
    app.run(debug=True)