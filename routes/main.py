
from flask import Blueprint, flash, redirect, render_template, session, request, url_for, jsonify, abort
from flask import current_app
from sqlalchemy import func
from models import Novel, Chapter, User, Bookmark
from functools import wraps
from extensions import db
from database import get_all_published_novels, delete_chapter_from_db, get_novel_statistics
import os
from werkzeug.utils import secure_filename
from forms.forms import NovelForm, ChapterForm
from datetime import datetime
from werkzeug.datastructures import FileStorage

# Create the Blueprint
main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
    
        if not user_id:
            flash('Please log in to access this page.', 'info') 
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
        
    return decorated_function

@main_bp.route('/')
def home():
    data = get_novel_statistics()

    if 'username' in session:
        user = session['username']
        return render_template('index.html', message=f"Welcome back, {user}!", active_page='home', data=data)
    return render_template('index.html', title='Novel Stream', active_page='home', data=data)

# ===================browse novels====================
@main_bp.route('/browse')
def browse():
    try:
        all_novels = get_all_published_novels()
    except Exception as e:
        print(f"Error accessing database during browse: {e}") 
        flash('Could not load the list of novels.', 'error')
        all_novels = []
    return render_template('library.html', novels=all_novels, active_page='browse')

# ===================user my_library====================
@main_bp.route('/my_library')
@login_required
def my_library():
    user_id = session.get('user_id')

    bookmarked_novels = db.session.query(Novel)\
        .join(Bookmark, Novel.id == Bookmark.novel_id)\
        .filter(Bookmark.user_id == user_id, Novel.status != 'draft')\
        .all()

    return render_template(
        'userLibrary.html', 
        novels=bookmarked_novels, 
        active_page='my_library'
    )



# ===================novel details page====================
def get_novel_details(novel_id, is_logged_in=False):    
    novel = db.session.get(Novel, novel_id)
    if not novel:
        return None, None, None, False

    current_user_id = session.get('user_id')
    is_author = (novel.author_id == current_user_id) if current_user_id else False

    if novel.status == 'draft' and not is_author:
        return None, None, None, False

    # Fetch chapters
    query = Chapter.query.filter_by(novel_id=novel_id)
    if not is_author:
        query = query.filter_by(is_published=True)
    
    chapters = query.order_by(Chapter.chapter_number).all()
    
    chapter_list = [{
        'id': c.id,
        'chapter_number': c.chapter_number,
        'title': c.title,
        'published_date': c.published_at,
        'is_published': c.is_published
    } for c in chapters]
    
    last_read_chapter_id = None
    has_bookmark = False
    
    if is_logged_in and current_user_id:
        bookmark = Bookmark.query.filter_by(
            user_id=current_user_id, 
            novel_id=novel_id
        ).first()
        
        if bookmark:
            has_bookmark = True
            last_read_chapter_id = bookmark.last_read_chapter_id

    return novel, chapter_list, last_read_chapter_id, has_bookmark


@main_bp.route('/novels/<int:novel_id>')
def novel(novel_id):
    is_logged_in = 'user_id' in session
    
    novel, chapters, last_read_id, has_bookmark = get_novel_details(novel_id, is_logged_in) 

    if novel is None:
        flash('Novel not found.', 'error')
        return redirect(url_for('main.browse')) 
    
    start_reading_chapter_id = last_read_id if last_read_id else (chapters[0]['id'] if chapters else None)
    
    return render_template(
        'novel.html', 
        novel=novel,
        author=novel.author,
        chapters=chapters,
        total_chapters=len(chapters),
        start_reading_chapter_id=start_reading_chapter_id, 
        has_bookmark=has_bookmark, # Now correctly passed from get_novel_details
        is_logged_in=is_logged_in,
        active_page='novel'
    )

# ===================API endpoint for paginated chapters====================
@main_bp.route('/api/novel/<int:novel_id>/chapters')
def get_chapters(novel_id):
# ... (get_chapters route remains the same)
    """API endpoint to get paginated chapters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Fetch chapters with pagination
    chapters_query = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.chapter_number)
    
    total_chapters = chapters_query.count()
    total_pages = (total_chapters + per_page - 1) // per_page  # Ceiling division
    
    chapters = chapters_query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Convert to JSON-friendly format
    chapters_data = [{
        'id': ch.id,
        'chapter_number': ch.chapter_number,
        'title': ch.title,
        'published_date': ch.published_at.strftime('%Y-%m-%d') if ch.published_at else None
    } for ch in chapters]
    
    return jsonify({
        'chapters': chapters_data,
        'page': page,
        'per_page': per_page,
        'total_chapters': total_chapters,
        'total_pages': total_pages
    })

# ===================profile===================
@main_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You must be logged in to view your profile.', 'warning')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    # 2. Fetch user details and their novels if have
    user = db.session.get(User, user_id) 
    user_novels = Novel.query.filter_by(author_id=user_id).order_by(Novel.title).all()
    
    # 4. Render the profile page
    return render_template(
        'profile.html', 
        user=user,
        novels=user_novels,
        active_page='profile'
    )

# ===================read chapter===================
@main_bp.route('/read/<int:novel_id>/chapter/<int:chapter_id>')
def read_chapter(novel_id, chapter_id):
    user_id = session.get('user_id')
    
    current_chapter = db.session.get(Chapter, chapter_id)
    novel = db.session.get(Novel, novel_id)

    if not current_chapter or not novel or current_chapter.novel_id != novel_id:
        flash('Chapter not found.', 'error')
        return redirect(url_for('main.index'))

    is_author = (user_id is not None and novel.author_id == user_id)

    # Novel Status Check if it fraft and not author
    if novel.status == 'draft' and not is_author:
        abort(404) 

    # Chapter checl
    if not current_chapter.is_published and not is_author:
        flash('This chapter is not yet available.', 'info')
        return redirect(url_for('main.novel', novel_id=novel_id))
    
    query = Chapter.query.filter_by(novel_id=novel_id)
    if not is_author:
        query = query.filter_by(is_published=True)
    
    all_chapters = query.order_by(Chapter.chapter_number).all()
    
    current_index = next((i for i, chap in enumerate(all_chapters) if chap.id == chapter_id), -1)

    if current_index == -1:
        abort(404)

    prev_chapter_id = all_chapters[current_index - 1].id if current_index > 0 else None
    next_chapter_id = all_chapters[current_index + 1].id if current_index < len(all_chapters) - 1 else None

    if user_id:
        bookmark = Bookmark.query.filter_by(user_id=user_id, novel_id=novel_id).first()
        if bookmark:
            bookmark.last_read_chapter_id = chapter_id
        else:
            new_bookmark = Bookmark(
                user_id=user_id, 
                novel_id=novel_id, 
                last_read_chapter_id=chapter_id,
                reading_status='reading'
            )
            db.session.add(new_bookmark)
        db.session.commit()
    
    return render_template(
        'chapter.html',
        novel=novel,
        chapter=current_chapter,
        prev_chapter_id=prev_chapter_id,
        next_chapter_id=next_chapter_id,
        is_author=is_author # Helpful for showing "Edit" buttons in the template
    )

# ====================create novel===================
# Helper function to save files safely
def save_picture(form_picture, novel_id):
    upload_dir = os.path.join(current_app.root_path, 'static/images/covers')
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = secure_filename(form_picture.filename)
    unique_filename = f'{novel_id}_{filename}'
    
    picture_path = os.path.join(upload_dir, unique_filename)
    form_picture.save(picture_path)
    
    return unique_filename

# // ====================edit novel===================
@main_bp.route('/studio/novel/edit/<int:novel_id>', methods=['GET', 'POST'])
@login_required 
def edit_novel(novel_id):
    user_id = session.get('user_id')
    
    novel = Novel.query.get_or_404(novel_id)

    if novel.author_id != user_id:
        flash('You are not authorized to edit this novel.', 'danger')
        return redirect(url_for('main.author_dashboard'))

    form = NovelForm(obj=novel)

    if form.validate_on_submit():
        novel.title = form.title.data
        novel.genre = form.genre.data
        novel.status = form.status.data
        novel.description = form.description.data

        if isinstance(form.cover_image.data, FileStorage) and form.cover_image.data.filename: 
            cover_filename = save_picture(form.cover_image.data, novel.id)
            novel.cover_image = cover_filename
        
        db.session.commit()
        
        flash('Novel details updated successfully!', 'success')
        return redirect(url_for('main.edit_novel', novel_id=novel.id))

    return render_template(
        'create_novel.html', 
        title=f'Edit Novel: {novel.title}', 
        form=form, 
        novel=novel, 
        is_editing=True,
        active_page='studio'
    )

@main_bp.route('/studio/dashboard')
@login_required
def author_dashboard():
    user_id = session.get('user_id')
    
    authors_novels = Novel.query.filter_by(author_id=user_id).order_by(Novel.created_date.desc()).all()
    
    novel_list = []
    for novel in authors_novels:
        
        chapter_count = novel.chapters.count() 
        
        novel_list.append({
            'id': novel.id,
            'title': novel.title,
            'status': novel.status,
            'chapters': chapter_count,
            'created_date': novel.created_date.strftime('%Y-%m-%d'),
        })

    # 3. Render the dashboard template
    return render_template(
        'author_dashboard.html',
        novels=novel_list,
        total_novels=len(novel_list),
        active_page='studio'
    )

@main_bp.route('/studio/novel/<int:novel_id>/chapters')
@login_required
def manage_chapters(novel_id):
# ... (manage_chapters route remains the same)
    user_id = session.get('user_id')
    
    novel = Novel.query.get_or_404(novel_id)
    
    # Authorization Check
    if novel.author_id != user_id:
        flash('You are not authorized to manage chapters for this novel.', 'danger')
        return redirect(url_for('main.author_dashboard'))

    # Fetch chapters, ordered by chapter number
    chapters = Chapter.query.filter_by(novel_id=novel_id).order_by(Chapter.chapter_number.asc()).all()

    return render_template(
        'manage_chapters.html',
        novel=novel,
        chapters=chapters,
        total_chapters=len(chapters),
        active_page='studio'
    )

@main_bp.route('/studio/novel/new', methods=['GET', 'POST'])
@login_required
def create_novel():
    form = NovelForm()
    
    if form.validate_on_submit():
        novel = Novel(
            title=form.title.data,
            author_id=session.get('user_id'),
            genre=form.genre.data,
            status=form.status.data,
            description=form.description.data
        )
        db.session.add(novel)
        db.session.flush()
        
        if form.cover_image.data:
            cover_filename = save_picture(form.cover_image.data, novel.id)
            novel.cover_image = cover_filename
            
        db.session.commit()
        
        flash('Novel created successfully! You can now start adding chapters.', 'success')
        return redirect(url_for('main.manage_chapters', novel_id=novel.id)) 
        
    return render_template('create_novel.html', 
                           title='Create Novel', 
                           form=form, 
                           active_page='studio')

@main_bp.route('/studio/novel/<int:novel_id>/chapter/new', methods=['GET', 'POST'])
@login_required
def create_chapter(novel_id):
    user_id = session.get('user_id')
    novel = Novel.query.get_or_404(novel_id)

    # Authorization Check
    if novel.author_id != user_id:
        flash('You are not authorized to add chapters to this novel.', 'danger')
        return redirect(url_for('main.author_dashboard'))

    form = ChapterForm()

    if form.validate_on_submit():
        if Chapter.query.filter_by(novel_id=novel_id, chapter_number=form.chapter_number.data).first():
            flash(f'Chapter number {form.chapter_number.data} already exists for this novel. Please choose a different number.', 'danger')
            
        else:
            is_published = form.is_published.data
            published_at = datetime.utcnow() if is_published else None 
            
            try:
                new_chapter = Chapter(
                    novel_id=novel_id,
                    chapter_number=form.chapter_number.data,
                    title=form.title.data,
                    content=form.content.data,
                    is_published=is_published,
                    published_at=published_at,
                    last_updated_date=datetime.utcnow() 
                )
                
                db.session.add(new_chapter)
                db.session.commit()
                
                flash(f'Chapter {new_chapter.chapter_number}: "{new_chapter.title}" saved successfully!', 'success')
                
                # Redirect to the chapter management list
                return redirect(url_for('main.manage_chapters', novel_id=novel_id))
            
            except Exception as e:
                db.session.rollback()
                print(f"Chapter creation error: {e}")
                flash('An error occurred while saving the chapter.', 'danger')

    if request.method == 'GET':
        max_chapter_num = db.session.query(db.func.max(Chapter.chapter_number)).filter_by(novel_id=novel_id).scalar()
        
        if not form.chapter_number.data:
            form.chapter_number.data = (max_chapter_num or 0) + 1

    return render_template(
        'create_chapter.html',
        title=f'New Chapter for {novel.title}',
        form=form,
        novel=novel,
        is_editing=False,
        active_page='studio'
    )



@main_bp.route('/studio/novel/<int:novel_id>/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chapter(novel_id, chapter_id):
    user_id = session.get('user_id') 

    novel = Novel.query.get_or_404(novel_id)
    chapter = Chapter.query.get_or_404(chapter_id)

    # Authorization Check
    if novel.author_id != user_id or chapter.novel_id != novel_id:
        flash('You are not authorized to edit this chapter.', 'danger')
        return redirect(url_for('main.author_dashboard'))

    form = ChapterForm(obj=chapter)

    if form.validate_on_submit():
        new_number = form.chapter_number.data
        
        duplicate = Chapter.query.filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number == new_number,
            Chapter.id != chapter_id 
        ).first()

        if duplicate:
            flash(f'Chapter number {new_number} is already taken by "{duplicate.title}".', 'danger')
        else:
            try:
                # Track status changes for publication dates
                was_published = chapter.is_published
                is_now_published = form.is_published.data
                
                # Update details
                chapter.chapter_number = new_number
                chapter.title = form.title.data
                chapter.content = form.content.data
                chapter.is_published = is_now_published
                chapter.last_updated_date = datetime.utcnow()
                
                # Publication logic
                if is_now_published and not was_published:
                    chapter.published_at = datetime.utcnow()
                elif not is_now_published and was_published:
                    pass
                
                db.session.commit()
                flash(f'Chapter {chapter.chapter_number}: "{chapter.title}" updated successfully!', 'success')
                return redirect(url_for('main.manage_chapters', novel_id=novel_id))
            
            except Exception as e:
                db.session.rollback()
                print(f"Chapter update error: {e}")
                flash('An error occurred while updating the chapter. Check chapter number uniqueness.', 'danger')

    return render_template(
        'create_chapter.html',
        title=f'Edit Chapter: {chapter.title}',
        form=form,
        novel=novel,
        chapter=chapter,
        is_editing=True,
        active_page='studio'
    )

@main_bp.route('/novel/<int:novel_id>/chapter/<int:chapter_id>/delete', methods=['POST'])
def delete_chapter(novel_id, chapter_id):    
    success = delete_chapter_from_db(novel_id, chapter_id)
    
    if success:
        flash('Chapter deleted successfully!', 'success')
    else:
        flash('Error: Chapter not found.', 'danger')
    return redirect(url_for('main.manage_chapters', novel_id=novel_id))



@main_bp.route('/studio/novel/<int:novel_id>/delete', methods=['POST'])
@login_required
def delete_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    if novel.author_id != session.get('user_id'):
        flash("Unauthorized", "danger")
        return redirect(url_for('main.author_dashboard'))
    
    # Optional: Delete cover image file from server here
    
    db.session.delete(novel)
    db.session.commit()
    flash(f"Novel '{novel.title}' deleted successfully.", "success")
    return redirect(url_for('main.author_dashboard'))


@main_bp.route('/api/library/toggle/<int:novel_id>', methods=['POST'])
@login_required
def toggle_bookmark_api(novel_id):
    user_id = session.get('user_id')
    
    existing_bookmark = Bookmark.query.filter_by(
        user_id=user_id, 
        novel_id=novel_id
    ).first()

    if existing_bookmark:
        db.session.delete(existing_bookmark)
        db.session.commit()
        return jsonify({
            "status": "removed",
            "message": "Removed from your library."
        })
    else:
        new_bookmark = Bookmark(
            user_id=user_id,
            novel_id=novel_id
        )
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({
            "status": "added",
            "message": "Added to your library!"
        })
    

@main_bp.route('/search')
def search():
    
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.browse'))
    
    results = Novel.query.filter(
        func.lower(Novel.title).like(f"%{query.lower()}%"),
        Novel.status.in_(['published', 'ongoing'])
    ).all()

    return render_template('search_result.html', novels=results, query=query)
