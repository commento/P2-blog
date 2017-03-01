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


# Page Rendering Handler
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()


# Ascii Art Database
class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


# Blog Post Database
class Post(db.Model):
    username = db.StringProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    liked_by = db.ListProperty(str, default=None)
    comments = db.ListProperty(str, default=None)
