# database.py

from extensions import db
from models import Novel, Chapter, Bookmark, User
from sqlalchemy import func

# =============================================================
#           NEW AUTHOR STUDIO QUERIES
# =============================================================

def get_chapters_for_management(novel_id):
    chapters = db.session.query(
        Chapter.id,
        Chapter.chapter_number,
        Chapter.title,
        Chapter.is_published,
        Chapter.last_updated_date 
    ) \
    .filter(Chapter.novel_id == novel_id) \
    .order_by(Chapter.chapter_number) \
    .all()
    
    return chapters


def get_next_chapter_number(novel_id):
    # Find the max chapter number for this novel
    max_chapter_num = db.session.query(
        func.max(Chapter.chapter_number)
    ).filter(Chapter.novel_id == novel_id).scalar()
    
    # Return 1 if no chapters exist, otherwise return max + 1
    return (max_chapter_num or 0) + 1

# =============================================================
#           EXISTING QUERIES (for reference)
# =============================================================

def get_user_library_items(user_id):  
    # 1. Subquery/CTE to calculate the total number of chapters per novel
    total_chapters_subquery = db.session.query(
        Chapter.novel_id, 
        func.count(Chapter.id).label('total_chapters_count')
    ).group_by(Chapter.novel_id).subquery()
    
    query_results = db.session.query(
        Novel.id.label('novel_id'),
        Novel.title,
        Novel.cover_image,
        Novel.author_id,
        Bookmark.reading_status.label('user_status'),
        Bookmark.last_read_chapter_id,
        total_chapters_subquery.c.total_chapters_count
    ) \
    .join(Bookmark, Novel.id == Bookmark.novel_id) \
    .outerjoin(total_chapters_subquery, Novel.id == total_chapters_subquery.c.novel_id) \
    .filter(Bookmark.user_id == user_id) \
    .all()

    # 3. Process results into a list of dictionaries for the template
    library_items = []
    for item in query_results:
        
        # Look up the last read chapter number
        # Note: This is an expensive query inside a loop, but functional for now.
        last_read_chapter = db.session.get(Chapter, item.last_read_chapter_id)
        progress_chapter_num = last_read_chapter.chapter_number if last_read_chapter else 0
        
        # Look up the author's username
        author = db.session.get(User, item.author_id)
        author_username = author.username if author else "Unknown Author"

        library_items.append({
            'id': item.novel_id,
            'title': item.title,
            'author': author_username,
            'cover_path': f'images/{item.cover_image}',
            'status': item.user_status.lower(), 
            'progress_chapter': progress_chapter_num,
            'total_chapters': item.total_chapters_count or 0, 
        })
        
    return library_items


def get_all_published_novels():
    total_chapters_subquery = db.session.query(
        Chapter.novel_id, 
        func.count(Chapter.id).label('total_chapters_count')
    ).filter(Chapter.is_published == True) \
     .group_by(Chapter.novel_id).subquery()
    
    # 2. Main Query: Select Novel details
    query_results = db.session.query(
        Novel.id.label('novel_id'),
        Novel.title,
        Novel.cover_image,
        Novel.description,
        Novel.genre,
        Novel.status,
        User.username.label('author_username'),
        total_chapters_subquery.c.total_chapters_count
    ) \
    .outerjoin(User, Novel.author_id == User.id) \
    .outerjoin(total_chapters_subquery, Novel.id == total_chapters_subquery.c.novel_id) \
    .filter(Novel.status.in_(['ongoing', 'completed'])) \
    .all()
    
    novel_list = []
    for item in query_results:
        novel_list.append({
            'id': item.novel_id,
            'title': item.title,
            'author': item.author_username if item.author_username else "Unknown Author",
            'cover_path': f'images/covers/{item.cover_image}' if item.cover_image else 'images/default-cover.jpg',
            'description': item.description,
            'genre': item.genre,
            'status': item.status.lower(), 
            'total_chapters': item.total_chapters_count or 0, 
        })
        
    return novel_list


def get_novel_details(novel_id, is_author=False):
    novel = db.session.get(Novel, novel_id)
    
    if not novel:
        return None

    # 3. Security Check: If the novel is a Draft, only the author should see it
    if novel.status.lower() == 'draft' and not is_author:
        return None
    
    author = db.session.get(User, novel.author_id) if novel.author_id else None
    
    query = Chapter.query.filter_by(novel_id=novel_id)
    
    if not is_author:
        query = query.filter_by(is_published=True)
        
    chapters = query.order_by(Chapter.chapter_number).all()
    
    chapter_list = []
    for chapter in chapters:
        chapter_list.append({
            'id': chapter.id,
            'chapter_number': chapter.chapter_number,
            'title': chapter.title,
            'published_date': chapter.published_at, 
            'word_count': len(chapter.content.split()) if chapter.content else 0,
            'is_published': chapter.is_published # Useful for the template
        })
    
    return {
        'id': novel.id,
        'title': novel.title,
        'author': author.username if author else "Unknown Author",
        'author_id': novel.author_id,
        'description': novel.description,
        'genre': novel.genre,
        'status': novel.status,
        'cover_path': f'images/covers/{novel.cover_image}' if novel.cover_image else 'images/default-cover.jpg',
        'created_date': novel.created_date,
        'updated_date': novel.updated_date,
        'total_chapters': len(chapters),
        'chapters': chapter_list
    }

def delete_chapter_from_db(novel_id, chapter_id):
    chapter_to_delete = Chapter.query.filter_by(id=chapter_id, novel_id=novel_id).first()
    
    if chapter_to_delete:
        deleted_number = chapter_to_delete.chapter_number
        
        db.session.delete(chapter_to_delete)
    
        subsequent_chapters = Chapter.query.filter(
            Chapter.novel_id == novel_id,
            Chapter.chapter_number > deleted_number
        ).all()
        
        for chap in subsequent_chapters:
            chap.chapter_number -= 1
            
        db.session.commit()
        return True
    return False

def get_novel_statistics():
    # gather novel statistics
    total_published_novels = db.session.query(func.count(Novel.id)).filter(Novel.status.in_(['ongoing', 'completed'])).scalar()
    total_users = db.session.query(func.count(User.id)).scalar()
    tatal_genres = db.session.query(Novel.genre).distinct().count()
    
    return {
        'total_users': total_users,
        'published_novels': total_published_novels,
        'total_genres': tatal_genres
    }