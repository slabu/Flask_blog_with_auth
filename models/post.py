from datetime import datetime

from db import db
from .tag import TagModel
from .user import UserModel


class PostModel(db.Model):
    __tablename__ = "post"

    post_id = db.Column(db.Integer, primary_key=True)
    post_name = db.Column(db.String(200), nullable=False)
    post_text = db.Column(db.String(1024), nullable=False)
    post_image = db.Column(db.String(1024), nullable=True)
    post_date_of_creation = db.Column(db.DateTime, nullable=False)
    post_date_of_edit = db.Column(db.DateTime, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    user = db.relationship('UserModel', backref=db.backref('user', lazy=True))

    def __init__(self, post_name, post_text, post_tags, user_id, **kwargs):
        self.post_name = post_name
        self.post_text = post_text
        self.post_image = kwargs['post_image_name']
        self.post_date_of_creation = datetime.now()
        self.post_date_of_edit = datetime.now()
        self.post_tags = [ TagModel(tag_name=tag.strip()) for tag in post_tags.split(',') ]
        self.user_id = user_id

    def json(self):
        return {
                "post_name": self.post_name, 
                "post_text": self.post_text,
                "post_image": self.post_image,
                "post_date_of_creation": self.post_date_of_creation,
                "post_date_of_edit": self.post_date_of_edit,
                "post_tags": self.post_tags
                }

    def parser(self):
        return {item:value for item, value in self.items()}

    @classmethod
    def find_by_id(cls, post_id):
        return PostModel.query.filter_by(post_id=post_id).first()

    @classmethod
    def find_by_image(cls, post_image):
        post_image = "image%"
        return PostModel.query.filter(PostModel.post_image.like(post_image)).order_by(PostModel.post_image.desc()).first()

    @classmethod
    def first_find_by_image(cls):
        return PostModel.query.filter_by(post_image!='None')

    @classmethod
    def get_all_posts(cls, page):
        return PostModel.query.order_by(PostModel.post_date_of_creation.desc()).paginate(page=page, per_page=10)

    @classmethod
    def get_all_posts_by_tag(cls, page, tag_name):
        current_tag_posts = TagModel.find_posts_for_tag_view(tag_name)
        post_list = [post.post_id for post in current_tag_posts]
        return PostModel.query.filter(PostModel.post_id.in_(post_list)).order_by(PostModel.post_date_of_creation.desc()).paginate(page=page, per_page=10)

    @classmethod
    def get_all_posts_by_user(cls, user_id, page):
        return PostModel.query.filter_by(user_id=user_id).order_by(PostModel.post_date_of_creation.desc()).paginate(page=page, per_page=10)

    @classmethod
    def get_my_posts(cls, user_id):
        return PostModel.query.filter_by(user_id=user_id).all()


    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    def update_the_row(self, new_values):

        self.query.filter(PostModel.post_id==self.post_id).update({'post_date_of_edit': datetime.now()})

        self.query.filter(PostModel.post_id==self.post_id).update(new_values)
        db.session.commit()
        