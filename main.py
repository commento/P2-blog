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

import re

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")


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
    if not username or not USER_RE.match(username):
        return False
    else:
        return True


def valid_email(email):
    if email == "" or EMAIL_RE.match(email):
        return True
    else:
        return False


def valid_password(password, verpass):
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
        items = self.request.get_all("food")
        self.render("index.html", items=items)

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
                self.render("index.html", nvu="Not valid username", name=username)
            elif not bool_password:
                self.render("index.html", nvp="Not valid password")
            elif not bool_email:
                self.render("index.html", nve="Not valid email", mail=email)
        else:
            self.redirect("/welcome?username=%s" % username)


class ThanksHandler(Handler):

    def get(self):
        username = self.request.get("username")
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
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class BlogHandler(Handler):

    def render_front(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
        self.render("blog.html", posts=posts)

    def get(self):
        self.render_front()


class NewPostHandler(Handler):

    def render_front(self, subject="", content="", error=""):

        self.render("newpost.html", subject=subject, content=content, error=error)

    def get(self):
        self.render_front()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if content and subject:
            a = Post(subject=subject, content=content)
            a.put()

            self.redirect("/blog/%s" % a.key().id())
        else:
            error = "we need both a subject and a content"
            self.render_front(subject, content, error)


class PostHandler(Handler):

    def get(self, id):
        key = db.Key.from_path("Post", int(id))
        post = db.get(key)
        post.content = post.content
        self.render("post.html", subject=post.subject, content=post.content, id=id)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/welcome', ThanksHandler),
    ('/front', FrontHandler),
    ('/blog', BlogHandler),
    ('/blog/newpost', NewPostHandler),
    ('/blog/([0-9]+)', PostHandler),

], debug=True)
