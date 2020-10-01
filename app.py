from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_images import resized_img_src, Images, resized_img_size
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import os

from db import db

from models.post import PostModel
from models.tag import TagModel
from models.user import UserModel



ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
IMAGES_PATH = 'static/uploads/images'

app = Flask(__name__)


app.config['SECRET_KEY'] = 'super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_IMAGES_DEST'] = 'static/uploads/images'
app.config['IMAGES_PATH'] = ['static/uploads/images']

manager = LoginManager(app)
uploaded_images = Images(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, images)

posts = []


@manager.user_loader
def load_user(user_id):
    return UserModel.query.get(user_id)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = PostModel.get_all_posts(page)
    return render_template('index.html', posts=posts, user=UserModel(), validate_user=load_user(current_user.get_id()))

@app.route('/tag/<string:tag_name>')
def posts_by_tag(tag_name):
    page = request.args.get('page', 1, type=int)
    tag = TagModel.query.filter_by(tag_name=tag_name).first_or_404()
    posts = PostModel.get_all_posts_by_tag(page, tag_name)
    return render_template('posts_by_tag.html', posts=posts, tag=tag, user=UserModel(), validate_user=load_user(current_user.get_id())) 

@app.route('/my_posts', methods=['GET'])
@login_required
def my_posts_view():
    page = request.args.get('page', 1, type=int)
    posts = PostModel.get_all_posts_by_user(current_user.user_id, page)    
    return render_template('my_posts.html', posts=posts, user=UserModel(), validate_user=load_user(current_user.get_id())) 

@app.route('/post_<int:post_id>')
def post_view(post_id):
    post = PostModel.find_by_id(post_id)
    if load_user(current_user.get_id()):

        if current_user.user_id == post.user_id:
            check_user = True
        else:
            check_user = False
    else:
        check_user = False
    return render_template('post_view.html', post=post, user=UserModel(), checked_user=check_user, validate_user=load_user(current_user.get_id()))

@app.route('/my_posts')
@login_required
def my_posts():
    posts = PostModel.get_my_posts(current_user.get_id())
    return render_template('my_posts.html', posts=posts)

@app.route('/edit_post_<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = PostModel.find_by_id(post_id)

    post_tags = [tag.tag_name for tag in post.post_tags]
    post_tags = ', '.join(post_tags)
    
    

    if load_user(current_user.get_id()):

        if current_user.user_id == post.user_id:
            check_user = True
        else:
            check_user = False
    else:
        check_user = False
    
    if request.method == 'GET':
        return render_template('edit_post.html', post=post, user=UserModel(), checked_user=check_user, validate_user=load_user(current_user.get_id()), post_tags=post_tags)
    
    if request.method == 'POST':        
        item = PostModel.find_by_id(post_id)

        if item.post_image != 'None':
            if request.files['post_image'].filename != '':                
                file = request.files['post_image']
        
                if file.filename:
                    new_image_name = post.post_image
                
                request.files['post_image'].filename = new_image_name
                os.remove('static/uploads/images/' + new_image_name)
                filename = images.save(request.files['post_image'])
            
            elif request.files['post_image'].filename == '' and 'image_edition' in request.form.keys():
                new_image_name = item.post_image
            
            else:
                new_image_name = 'None'
        else:
            if request.files['post_image'].filename != '':
                '''
                file = request.files['post_image']

                if file.filename:
                    new_image_name = post.post_image
                '''
                file = request.files['post_image']

                new_image_name = f"image_0.{file.filename.split('.')[1]}"
            
                changeable_name = PostModel.find_by_image(new_image_name)

                if changeable_name:
                    new_name = changeable_name.post_image.rsplit('_')
                    new_name[1] = new_name[1].rsplit('.')
                    new_name[1][0] = str(f"_{int(new_name[1][0]) + 1}.")
                    new_image_name = rebuild(new_name)

                request.files['post_image'].filename = new_image_name
                os.remove('static/uploads/images/' + new_image_name)
                filename = images.save(request.files['post_image'])
            else:
                new_image_name = 'None'

        input_data = PostModel.parser(request.form)
        input_data['post_image'] = new_image_name
        
        if 'image_name' in input_data.keys():
            input_data.pop('image_name')

        if 'image_edition' in input_data.keys():
            input_data.pop('image_edition')

        for tag in post_tags.split(', '):
            edited_tag = TagModel.find_by_name(tag_name=tag, post_id=item.post_id)
            if edited_tag:
                edited_tag.delete_from_db()
        
        for tag in request.form['post_tags'].split(', '):
            new_tag = TagModel(tag_name=tag, post_id=item.post_id)
            new_tag.update_tags(tag_name=tag, post_id=item.post_id)
        
        
          
        input_data.pop('post_tags')

        post.update_the_row(input_data)
    
    return redirect(url_for('post_view', post_id=item.post_id))
        

@app.route('/new_post', methods=['GET'])
@login_required
def add_post():
    if request.method == 'GET':
        return render_template('add_post.html', user=UserModel(), validate_user=load_user(current_user.get_id()))

def rebuild(name):
    new_name = []
    for item in name:
        if type(item) != list:
            new_name.append(item)
        else:
            rebuild(item)
    new_name.append(''.join(item))
    return ''.join(new_name)

@app.route('/add_new_post', methods=['POST'])
@login_required
def add_new_post():

    if request.method == 'POST' and 'post_image' in request.files:
        file = request.files['post_image']
        
        if file.filename:
            new_image_name = f"image_0.{file.filename.split('.')[1]}"
            
            changeable_name = PostModel.find_by_image(new_image_name)

            if changeable_name:
                new_name = changeable_name.post_image.rsplit('_')
                new_name[1] = new_name[1].rsplit('.')
                new_name[1][0] = str(f"_{int(new_name[1][0]) + 1}.")
                new_image_name = rebuild(new_name)
            
            request.files['post_image'].filename = new_image_name
            filename = images.save(request.files['post_image'])    
        else:
            new_image_name = 'None'
        
        input_data = PostModel.parser(request.form)

        item = PostModel(post_image_name=new_image_name, user_id=current_user.get_id(), **input_data)
        item.save_to_db()

    return redirect(url_for('post_view', post_id=item.post_id))


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    login = request.form.get('login')
    password = request.form.get('password')

    if login and password:
        user = UserModel.find_by_login(login)

        if user and check_password_hash(user.user_password, password):
            login_user(user)

            next_page = request.args.get('next')
            
            if next_page == None:
                return redirect(url_for('index'))
            return redirect(next_page)
        else:
            flash("Login or password is not correct!")
    else:
        flash("Please fill login and password fields!")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    login = request.form.get('login')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if request.method == 'POST':
        if not login or not password or not password2:
            flash("Please, fill all the fields!")
        elif password != password2:
            flash("Passwords are not equal!")
        else:
            hash_pwd = generate_password_hash(password)
            new_user = UserModel(user_login=login, user_password=hash_pwd)

            new_user.save_to_db()

            return redirect(url_for('login_page'))
    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url )
    return response

if __name__ == "__main__":
    db.init_app(app)
    app.run(port=5000, debug=True)