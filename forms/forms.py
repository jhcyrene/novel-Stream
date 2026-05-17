# File: forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length,  Optional, NumberRange

class NovelForm(FlaskForm):
    title = StringField('Novel Title', validators=[DataRequired(), Length(min=1, max=100)])
    
    # Example Genres (adjust as needed)
    genre = SelectField('Genre', choices=[
        ('fantasy', 'Fantasy'), 
        ('scifi', 'Science Fiction'), 
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('historical', 'Historical Fiction'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    
    status = SelectField('Novel Status', choices=[
        ('ongoing', 'Ongoing (Publishing Chapters)'), 
        ('completed', 'Completed'),
        ('draft', 'Draft (Not Public)')
    ], validators=[DataRequired()])
    
    description = TextAreaField('Synopsis / Description', validators=[DataRequired(), Length(min=20, max=5000)])
    
    cover_image = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!'), 
        # Optionally, make this field required: DataRequired()
    ])
    
    submit = SubmitField('Create Novel')

class ChapterForm(FlaskForm):
    chapter_number = IntegerField(
        'Chapter Number',
        validators=[
            DataRequired(message="Chapter number is required."),
            NumberRange(min=1, message="Chapter number must be 1 or higher.")
        ]
    )
    
    title = StringField(
        'Chapter Title',
        validators=[
            DataRequired(message="A chapter title is required."),
            Length(min=3, max=100, message="Title must be between 3 and 100 characters.")
        ]
    )
    
    content = TextAreaField(
        'Chapter Content',
        validators=[
            DataRequired(message="Chapter content cannot be empty.")
        ],
        description="Write the full content of your chapter here. Formatting is now supported!"
    )
    
    # Allows the author to save as a draft or publish immediately
    is_published = BooleanField(
        'Publish Chapter Immediately',
        default=False,
        validators=[Optional()]
    )

    submit = SubmitField('Save Chapter')