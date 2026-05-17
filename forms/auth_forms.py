from wtforms import Form, StringField, PasswordField, validators # Note: We don't need 'Form' anymore
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
from flask_wtf import FlaskForm # This is the correct base class to use

MIN_USERNAME_LENGTH = 4
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

class LoginForm(FlaskForm):
# -------------------------------------------
    email = StringField(
        'Email Address',
        [
            DataRequired(message='Email is required.'),
            Email(message='Must be a valid email address.'),
        ],
        description='you@example.com'
        
    )

    # Password 
    password = PasswordField(
        'Password',
        [
            DataRequired(message='Password is required.'),
            Length(min=MIN_PASSWORD_LENGTH, max=MAX_PASSWORD_LENGTH,
                message=f'Password must be at least {MIN_PASSWORD_LENGTH} characters long.'),
            Regexp(
                r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$',
                message="Password must contain at least one letter and one number."
            )
        ]
    )


class RegistrationForm(FlaskForm):
    name = StringField(
        'Full Name',
        [
            DataRequired(message='Name is required.'),
            Length(min=MIN_USERNAME_LENGTH, max=MAX_USERNAME_LENGTH,
                   message=f'Name must be between {MIN_USERNAME_LENGTH} and {MAX_USERNAME_LENGTH} characters.')
        ]
    )

    email = StringField(
        'Email Address',
        [
            DataRequired(message='Email is required.'),
            Email(message='Must be a valid email address.')
        ],
        description='you@example.com'
    )
    password = PasswordField(
        'Password',
        [
            DataRequired(message='Password is required.'),
            Length(min=MIN_PASSWORD_LENGTH, max=MAX_PASSWORD_LENGTH,
                   message=f'Password must be at least {MIN_PASSWORD_LENGTH} characters long.'),
            Regexp(
                r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$',
                message="Password must contain at least one letter and one number."
            )
        ]
    )
    
    confirm = PasswordField(
        'Repeat Password',
        [
            EqualTo('password', message='Passwords must match.')
        ]
    )