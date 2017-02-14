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

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape= True)

ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz' #26
ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def apply_rot13(text):
    test = ""
    for i in text:
    	if i.isupper():
    		test += ascii_uppercase[(ascii_uppercase.find(i) + 13) %26]
    	elif i.islower():
    		test += ascii_lowercase[(ascii_lowercase.find(i) + 13) %26]
    	else:
    		test += i
    return test


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
    	self.render("index.html", items = items)
        #self.response.write(form)

    def post(self):
    	text = self.request.get('text')
    	text = str(text)

    	text=apply_rot13(text)
    	self.render("index.html", ciao=text)


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
