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

import string
import webapp2

from models import *

from google.appengine.ext import db


# Signup Page Handler
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


# Login Page Handler
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


# Logout Page Handler
class LogoutPage(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            self.render("logout.html", username=username)
            self.response.headers.add_header('Set-Cookie', 'username=; Path=/')
        else:
            self.render("logout.html", username="Username Not Found")


# Welcome Page Handler
class ThanksHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if check_secure_val(username):
            username = username.split('|')[0]
        else:
            self.redirect("/signup")

        self.render("thanks.html", username=username)


# Ascii Art Page Handler
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


# Main Page Blog Handler
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


# New Blog Post Page Handler
class NewPostHandler(Handler):

    def render_front(self, subject="", content="", error=""):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            self.render("newpost.html", username=username, subject=subject,
                        content=content, error=error)
        else:
            self.redirect("/login")

    def get(self):
        self.render_front()

    def post(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            subject = self.request.get("subject")
            content = self.request.get("content")

            if content and subject:
                p = Post(username=username, subject=subject,
                         content=content)
                p.put()

                self.redirect("/blog/%s" % p.key().id())
            else:
                error = "we need both a subject and a content"
                self.render_front(subject, content, error)
        else:
            self.redirect("/login")

# Delete Blog Post Page Handler
class DeletePostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            id = self.request.get('id')
            post = Post.get_by_id(int(id))
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            if username == post.username:
                post.delete()
            else:
                id = "You cannot delete this post"
            self.render("deletepost.html", id=id)
        else:
            self.redirect("/login")


# Edit Blog Post Page Handler
class EditPostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            id = self.request.get('id')
            post = Post.get_by_id(int(id))
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            self.render("editpost.html",
                        username=post.username, subject=post.subject,
                        content=post.content)
        else:
            self.redirect("/login")

    def post(self):
        id = self.request.get('id')
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            p = Post.get_by_id(int(id))
            if not p:
                self.error(404)
                return self.redirect('not_found.html')
            if p.username != username:
                return self.redirect("/blog")
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


# App Front Page Handler
class FrontPage(Handler):

    def get(self):
        self.render("main.html")


# Single Blog Post Page Handler
class PostHandler(Handler):

    def get(self, id):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            self.render("post.html", username=username, subject=post.subject,
                        content=post.content, id=id)
        else:
            self.redirect("/login")


# Like Feature Handler
class LikePostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            if post.username == username:
                return self.redirect('/blog')
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
            self.redirect("/login")


# Comment Feature Handler
class CommentPostHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            self.render("comment.html", username=username,
                        subject=post.subject,
                        content=post.content, id=id)
        else:
            self.redirect("/login")

    def post(self):
        id = self.request.get('id')
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            comment = self.request.get("comment")
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            post.comments.append(username + "-" + comment)
            post.put()
            self.redirect("/blog")
        else:
            self.redirect("/login")


# Edit Comment Feature Handler
class EditCommentHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            username = username.split('|')[0]
            id = self.request.get('id')
            comment = self.request.get('commented')
            print(comment)
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            commentToEdit = ""   
            for com in post.comments:
                print(com)
                if com == comment:
                    commentToEdit = comment.split('-')[1]
            if commentToEdit == "":
                print("ciao")
                return self.redirect("/blog")
            self.render("comment.html", username=username,
                        subject=post.subject,
                        content=post.content, comment=commentToEdit, id=id)
        else:
            self.redirect("/login")

    def post(self):
        id = self.request.get('id')
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            comment = self.request.get("comment")
            commented = self.request.get("commented")
            id = self.request.get('id')
            key = db.Key.from_path("Post", int(id))
            post = db.get(key)
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            for idx, com in enumerate(post.comments):
                if commented == com:
                   post.comments[idx] = username + "-" + comment
            post.put()
            self.redirect("/blog")
        else:
            self.redirect("/login")


# Delete Comment Feature Handler
class DeleteCommentHandler(Handler):

    def get(self):
        username = self.request.cookies.get("username")
        if username:
            # check username and related hash
            if check_secure_val(username):
                username = username.split('|')[0]
            else:
                self.redirect("/signup")
            id = self.request.get('id')
            comment = self.request.get('commented')
            post = Post.get_by_id(int(id))
            if not post:
                self.error(404)
                return self.redirect('not_found.html')
            for idx, comment in enumerate(post.comments):
                if commented == comment and (username == comment.split('-')[0] or username == post.username):
                    post.comments[idx].delete()
                else:
                    comment = "You cannot delete this comment"
            self.render("deletecomment.html", comment=comment)
        else:
            self.redirect("/login")


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
    ('/blog/editcomment', EditCommentHandler),
    ('/blog/deletecomment', DeleteCommentHandler),
], debug=True)
