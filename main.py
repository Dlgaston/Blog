from functools import wraps
import os
from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

from forms import CreatePostForm, RegisterUserForm, LoginUserForm, CommentForm
from flask_gravatar import Gravatar

from dotenv import load_dotenv

#Load .env files
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRET_KEY"]
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URI"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#User Session Logins
login_manager = LoginManager()
login_manager.init_app(app)

##CONFIGURE TABLES

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    # Creates reference to the BlogPost object.
    posts = relationship("BlogPost", back_populates="author")

    # Creates reference to the Comment object
    comments = relationship("Comment", back_populates="author")

    def is_authenticated(self):
        return True
    def is_anonymous(self):
        return False
    def is_active(self):
        return True
    def get_id(self):
        return str(self.id)

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)

    # References auth id to foreignkey of users table
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")

    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    # creates foreign key for author
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")
    # creates foreign key for blogPost object.
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    body = db.Column(db.String(), nullable=False)
    date = db.Column(db.String(), nullable=False)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

with app.app_context():
    db.create_all()

 # Create admin decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #If id is not 1 then return abort with 403 error
        if current_user.id != 2:
            return abort(403)
        #Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter_by(id=user_id).first()

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    newUserForm = RegisterUserForm()

    if newUserForm.validate_on_submit():
        password = newUserForm.password.data
        name = newUserForm.name.data
        email = newUserForm.email.data
        if db.session.query(User).filter_by(email=email).first() is None:

            new_user = User()
            new_user.name = name
            new_user.email = email
            new_user.password = generate_password_hash(password=password, salt_length=12)
            db.session.add(new_user)
            db.session.commit()
            login_user(user=new_user)
            return redirect(url_for("get_all_posts"))
        else:
            flash("Email is already registered. Please Log in.")
            return redirect(url_for("login"))
    return render_template("register.html", form=newUserForm)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginUserForm()

    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        user=db.session.query(User).filter_by(email=email).first()
        if user is not None:
            if check_password_hash(user.password,password):
                login_user(user=user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Password does not match, please try again.")
                return render_template("login.html", form=login_form)
        else:
            flash("Email not found. Please try another email, or register.")
            return render_template("login.html", form=login_form)
    return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods = ["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    post_comments = db.session.query(Comment).filter_by(post_id=post_id).all()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Please log-in before commenting")
            return redirect(url_for("login"))
        else:
            body = comment_form.body.data
            new_comment = Comment(
                author=current_user,
                parent_post=requested_post,
                body=body,
                date=date.today().strftime("%B %d, %Y")
            )
            db.session.add(new_comment)
            db.session.commit()
            return render_template("post.html", post=requested_post, form=comment_form)
    return render_template("post.html", post=requested_post, form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@login_required
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@login_required
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>", methods=["DELETE"])
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
