# My Personal Blog Website.
* https://bart-blog.herokuapp.com/
* An End-to-End application, managed from development through to production.


## Functionality
* Users need to register/login in order to comment on posts.
* Passwords are securely encoded with hashing and salting methods.
* Only Admin users can create and delete posts.
* Users can get in contact with the the owner(me) regarding any enquiries and see what the owner is about.
* The App makes use of CKeditor (for creating posts and comments); a WYSIWYG rich text editor which enables writing content directly inside of web pages or online applications.
* (Production) WSGI server is setup with Gunicorn to run the Live Python Application on Heroku. PostgreSQL database is used for production.
* (Development) Development and testing is done locally with a SQLite database.

## Topics covered

* Python, HTML, CSS, Heroku, SQL
* Flask Web Framework 
* SQL Databases
* Decorators
* OOP
* Functions

## Packages
* See requirements.txt for all packages and dependencies used.
