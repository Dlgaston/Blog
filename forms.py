from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import InputRequired, URL, Email
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired()])
    subtitle = StringField("Subtitle", validators=[InputRequired()])
    img_url = StringField("Blog Image URL", validators=[InputRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[InputRequired()])
    submit = SubmitField("Submit Post")

class RegisterUserForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired("Please enter your display name")])
    email = StringField("Email",validators=[InputRequired("Please enter your email"), Email("Valid Email Required")])
    password = PasswordField("Password", validators=[InputRequired("Please enter a password")])
    submit = SubmitField("Register Account")

class LoginUserForm(FlaskForm):
    email = StringField("Email",validators=[InputRequired("Please enter your email"), Email("Valid Email Required")])
    password = PasswordField("Password", validators=[InputRequired("Please enter a password")])
    submit = SubmitField("Login")

class CommentForm(FlaskForm):
    body = CKEditorField("Comment", validators=[InputRequired()])
    submit = SubmitField("Add Comment")