# P2 Multi User Blog

Instruction:
1. Clone the repository: https://github.com/commento/P2-blog
2. Install Google App Engine Standard Environment for Python 2.7.
   Follow the instruction at the link: https://cloud.google.com/appengine/docs/standard/python/
3. Open terminal and go to the project folder.
4. Type command dev_appserver.py app.yaml to run the project.
5. Open browser and go to localhost:8080.

files:

- main.py

template html:
- index.html      : /signup
- login.html      : /login
- logout.html     : /logout
- blog.html       : /blog
- newpost.html    : /blog/newpost
- editpost.html   : /blog/edit
- deletepost.html : /blog/delete
- post.html       : /blog/(post_id)


The app is implemented in main.py file and it is reacheable from the url:
https://p2-udacity.appspot.com/



