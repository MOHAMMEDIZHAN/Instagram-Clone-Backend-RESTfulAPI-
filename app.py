#Importing the necessary packages
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

#Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Izhanmd@10@localhost/instagram_clone'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

#Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    posts = db.relationship('Post', backref='user', lazy=True)
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caption = db.Column(db.String(255))
    media_url = db.Column(db.String(255))
    music_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50))
    datetime_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment = db.Column(db.String(255))

#Routes

#User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(username=data['username'], email=data['email'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

#User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if(user and check_password_hash(user.password, data['password'])):
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

#Post a Photo/Video
@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.json
    new_post = Post(
        caption=data['caption'],
        media_url=data['media_url'],
        music_url=data['music_url'],
        category=data['category'],
        datetime_posted=data['datetime_posted'],
        user_id=data['user_id']
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully'}), 201

#View a User Profile
@app.route('/profile/<int:user_id>', methods=['GET'])
def view_profile(user_id):
    user = User.query.get(user_id)
    if user:
        posts = [{'id':post.id, 'caption': post.caption} for post in user.posts]
        return jsonify({'username':user.username, 'email': user.email, 'posts': posts}), 200
    return jsonify({'message': 'User not found'}), 404

#Follow other users
@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.json
    follow = Follow(follower_id=data['follower_id'], followed_id=data['followed_id'])
    db.session.add(follow)
    db.session.commit()
    return jsonify({'message': 'User has been followed successfully'}), 201

#Posts by logged in users
@app.route('/user_posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    posts = Post.query.filter_by(user_id=user_id).all()
    return jsonify([{'id':Post.id, 'caption': Post.caption, 'datetime_posted': Post.datetime_posted} for post in posts]), 200

#Posts by other users
@app.route('/all_posts', methods=['GET'])
def get_all_posts():
    posts = Post.query.all()
    return jsonify([{'id': Post.id, 'caption': Post.caption, 'user_id': Post.user_id} for post in posts]), 200

#Get details of a specific post
@app.route('/post_details/<int:post_id>', methods=['GET'])
def get_post_details(post_id):
    post = Post.query.get(post_id)
    if post:
        likes = Like.query.filter_by(post_id=post_id).count()
        comments = Comment.query.filter_by(post_id=post_id).count()
        return jsonify({
            'id': post.id,
            'caption': post.caption,
            'likes': likes,
            'comments': comments
        }), 200
    return jsonify({'message': 'Post not found'}), 404

#Like a Post
@app.route('/like', methods=['POST'])
def like_post():
    data = request.json
    like = Like(user_id=data['user_id'], post_id=data['post_id'])
    db.session.add(like)
    db.session.commit()
    return jsonify({'message': 'Post liked successfully'}), 201

#Get all users who liked a particular post
@app.route('/likes/<int:post_id', methods=['GET'])
def get_post_likes(post_id):
    likes = Like.query.filter_by(post_id=post_id).all()
    return jsonify([{'user_id': Like.user_id} for like in likes]), 200

#Comment on a post
@app.route('/comment', methods=['POST'])
def comment_post():
    data = request.json
    comment = Comment(user_id=data['user_id'], comment_id=data['comment_id'])
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully'}), 201

#Get all users who commented a particular post
@app.route('/comments/<int:post_id>', methods=['GET'])
def get_post_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    return jsonify([{'user_id': Comment.user_id, 'comment': comment.comment} for comment in comments]), 200

#Get user feed based on users they follow in descending order
@app.route('/feed/<int:user_id>', methods=['GET'])
def user_feed(user_id):
    followed_users = Follow.query.filter_by(follower_id=user_id).all()
    followed_ids = [follow.followed_id for follow in followed_users]
    posts = Post.query.filter(Post.user_id.in_(followed_ids)).order_by(Post.datetime_posted.desc()).all()
    return jsonify([{'id': post.id, 'caption': post.caption, 'user_id': post.user_id}for post in posts]), 200

#initialize database
with app.app_context():
    db.create_all()

#Run the app
if __name__ == 'main':
    app.run(debug=True)