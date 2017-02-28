# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import jinja2
import webapp2
import string
import hashlib

import re

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def hash_str(s):
    return hashlib.sha256(s).hexdigest()


def make_secure_val(s):
    return s + '|' + hash_str(s)


def check_secure_val(h):
    v = h.partition('|')
    if hash_str(v[0]) == v[2]:
        return v[0]


def apply_rot13(text):
    test = ""
    for i in text:
        if i.isupper():
            test += ascii_uppercase[(ascii_uppercase.find(i) + 13) % 26]
        elif i.islower():
            test += ascii_lowercase[(ascii_lowercase.find(i) + 13) % 26]
        else:
            test += i
    return test


def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    if not username or not USER_RE.match(username):
        return False
    else:
        return True


def valid_email(email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    if email == "" or EMAIL_RE.match(email):
        return True
    else:
        return False


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()


def checkUserPass(username, password):
    users = db.GqlQuery("SELECT * FROM User")
    for user in users:
        if user.username == username and user.password == hash_str(password):
            return True


def checkUsername(username):
    users = db.GqlQuery("SELECT * FROM User")
    for user in users:
        if user.username == username:
            return False


def valid_password(password, verpass):
    PASS_RE = re.compile(r"^.{3,20}$")
    if password and PASS_RE.match(password) and password == verpass:
        return True
    else:
        return False


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):

    def get(self):
        self.render("index.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        bool_username = valid_username(username)
        bool_password = valid_password(password, verify)
        bool_email = valid_email(email)

        if not (bool_username and bool_password and bool_email):
            if not bool_username:
                stringNVU = "Not valid username"
                self.render("index.html", nvu=stringNVU, name=username)
            elif not bool_password:
                stringNVP = "Not valid password"
                self.render("index.html", nvp=stringNVP)
            elif not bool_email:
                stringNVE = "Not valid email"
                self.render("index.html", nve=stringNVE, mail=email)
        elif checkUsername(username) is False:
            stringAUU = "Already used username"
            self.render("index.html", nvu=stringAUU, name=username)
        else:
            u = User(username=username,
                     password=hash_str(password), email=email)
            u.put()
            cookie_username = make_secure_val(username)
            self.response.headers.add_header('Set-Cookie',
                                             'username=%s; Path=/'
                                             % str(cookie_username))
            self.redirect("/welcome")


class LoginPage(Handler):

    def get(self):
        self.render("login.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        checkup = checkUserPass(username, password)

        if not checkup:
            stringNVUP = "Not valid username or Not valid password"
            self.render("login.html", nvu=stringNVUP, name=username)
        else:
            cookie_username = make_secure_val(username)
            self.response.headers.add_header('Set-Cookie',
                                             'username=%s; Path=/'
                                             % str(cookie_username))
            self.redirect("/welcome")


class LogoutPage(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            self.render("logout.html", username=username)
            self.response.headers.add_header('Set-Cookie', 'username=; Path=/')
        else:
            self.render("logout.html", username="Username Not Found")


class ThanksHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if check_secure_val(username):
            username = username.split('|')[0]
        else:
            self.redirect("/signup")

        self.render("thanks.html", username=username)


class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class FrontHandler(Handler):

    def render_front(self, title="", art="", error=""):

        arts = db.GqlQuery("SELECT * FROM Art ORDER BY created DESC")
        self.render("front.html", title=title, art=art, error=error, arts=arts)

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if art and title:
            a = Art(title=title, art=art)
            a.put()

            self.redirect("/front")
        else:
            error = "we need both a title and an artwork"
            self.render_front(title, art, error)


class Post(db.Model):
    username = db.StringProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    liked_by = db.ListProperty(str, required=True, default=None)
    comments = db.ListProperty(str, default=None)


class BlogHandler(Handler):

    def render_front(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY "
                            "created DESC LIMIT 10")

        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            self.render("blog.html", username=username, posts=posts)
        else:
            self.redirect("/signup")

    def get(self):
        self.render_front()


class NewPostHandler(Handler):

    def render_front(self, subject="", content="", error=""):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            self.render("newpost.html", username=username, subject=subject,
                        content=content, error=error)
        else:
            self.redirect("/signup")

    def get(self):
        self.render_front()

    def post(self):
        username = self.request.cookies.get("username")
        username = username.split('|')[0]
        subject = self.request.get("subject")
        content = self.request.get("content")
        liked_by = [username]

        if content and subject:
            p = Post(username=username, subject=subject,
                     content=content, liked_by=liked_by)
            p.put()

            self.redirect("/blog/%s" % p.key().id())
        else:
            error = "we need both a subject and a content"
            self.render_front(subject, content, error)


class DeletePostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            id = self.request.get('id')
            post = Post.get_by_id(int(id))
            if not post:
                self.error(404)
                return
            post.delete()
            self.render("deletepost.html", id=id)
        else:
            self.redirect("/login")


class EditPostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            id = self.request.get('id')
            post = Post.get_by_id(int(id))
            self.render("editpost.html",
                        username=post.username, subject=post.subject,
                        content=post.content)
        else:
            self.redirect("/login")

    def post(self):
        id = self.request.get('id')
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            p = Post.get_by_id(int(id))
            if p.username != username:
                self.redirect("/blog")
            subject = self.request.get("subject")
            content = self.request.get("content")

            if content and subject:
                p.subject = subject
                p.content = content
                p.put()

                self.redirect("/blog/%s" % p.key().id())
            else:
                error = "we need both a subject and a content"
                self.render("editpost.html",
                            username=post.username, subject=post.subject,
                            content=post.content, error=error)
        else:
            self.redirect("/login")


class FrontPage(Handler):

    def get(self):
        self.render("main.html")


class PostHandler(Handler):

    def get(self, id):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            self.render("post.html", username=username, subject=post.subject,
                        content=post.content, id=id)
        else:
            self.redirect("/signup")


class LikePostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            likes = post.liked_by
            find = False
            for like in likes:
                if like == username:
                    # unlike - remove username
                    post.liked_by.remove(username)
                    find = True
            if find is False:
                # like - add username
                post.liked_by.append(username)
            post.put()
            self.redirect("/blog")
        else:
            self.redirect("/signup")

class CommentPostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            self.render("comment.html", username=username, subject=post.subject,
                        content=post.content, id=id)
        else:
            self.redirect("/signup")

    def post(self):
        id = self.request.get('id')
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            comment = self.request.get("comment")
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            post.comments.append(username + " - " + comment)
            post.put()
            self.redirect("/blog")
        else:
            self.redirect("/signup")


app = webapp2.WSGIApplication([
    ('/', FrontPage),
    ('/signup', MainPage),
    ('/login', LoginPage),
    ('/logout', LogoutPage),
    ('/welcome', ThanksHandler),
    ('/front', FrontHandler),
    ('/blog', BlogHandler),
    ('/blog/newpost', NewPostHandler),
    ('/blog/delete', DeletePostHandler),
    ('/blog/([0-9]+)', PostHandler),
    ('/blog/edit', EditPostHandler),
    ('/blog/like', LikePostHandler),
    ('/blog/comment', CommentPostHandler),
], debug=True)
