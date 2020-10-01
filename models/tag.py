from db import db


class TagModel(db.Model):
    __tablename__ = "tag"
    
    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(50), nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.post_id'), nullable=False)
    post = db.relationship('PostModel', backref=db.backref('post_tags', lazy=True))

    def update_tags(self, tag_name, post_id):
        self.tag_name = tag_name
        self.post_id = post_id
        
        db.session.add(self)
        db.session.commit()

    @classmethod
    def find_by_name(cls, tag_name, post_id):
        return TagModel.query.filter_by(tag_name=tag_name, post_id=post_id).first()

    @classmethod
    def find_posts_for_tag_view(cls, tag_name):
        return TagModel.query.filter_by(tag_name=tag_name).all()

    @classmethod
    def delete_tag(self):
        item_to_delete = TagModel.query.filter_by(tag_name=tag).first()
        db.session.delete(item_to_delete)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_all_tags(cls):
        return TagModel.query.all()