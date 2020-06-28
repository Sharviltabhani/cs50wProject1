import os, json, requests

from flask import Flask, session, render_template, redirect, flash
from flask import request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256


app = Flask(__name__)

# Set environment variables
os.environ['DATABASE_URL'] = 'postgres://ghpbuuqthyjnlq:b09cbc9f5ea657890f4dd7d80811a6803b9e9d0cd4a59a31bc0772240149bd32@ec2-54-246-85-151.eu-west-1.compute.amazonaws.com:5432/dfo7tn78867kis'


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
goodreads_key = ''
book1 = "global"



#Index (main route)

@app.route("/")
def index():
      if request.method == "POST":

        if not request.form.get("username"):
            return render_template("error.html", error="username field not filled in")

        if not request.form.get("password"):
            return render_template("error.html", error="Must fill in password")

        username = request.form.get("username")
        password = request.form.get("password")
        userrow = db.execute("SELECT passwordhash FROM users WHERE username = :username",{"username": username}).fetchone()

        if not userrow:
            return render_template("error.html", error="We could not find that username. Have you signed up yet?")

        for row in userrow:
            userhash = row

        if not check_password(userhash, password):
            return render_template("error.html", error="password incorrect.")

        else:
            session["user"] = username
            return redirect("/login")

      else:
        if session.get("user") is None:
            return render_template("index.html")

        else:
            return redirect("/login")

#Signup user
@app.route("/signup", methods=["GET", "POST"])
def signup():
    session.clear()
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

    #    if not request.form.get("username"):
        #    return render_template("signup.html", danger_msg = "Please enter your username.")
        #elif not request.form.get("password"):
    #        return render_template("signup.html", danger_msg = "Please enter your password.")
    #    elif not request.form.get("confirm"):
    #        return render_template("signup.html", danger_msg = "Please confirm your password.")
    #    elif not request.form.get("password") == request.form.get("confirm") :
    #        return render_template("signup.html", danger_msg = "password do not match.")
        #elif not(request.form.get("password")) < 8:
            #return render_template("signip.html", danger_msg = "password must be al least 8 characters long.")
        if( db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount>0 ):
            return render_template("error.html", message="username already exsists.")
        else:
            hashedpassword = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash);", {"username": username, "hash": hashedpassword})
            db.commit()
            session["user_name"] = username
            session["logged_in"] = True
            return render_template("search.html")
            return redirect("/login")
    else:
        return render_template("signup.html")









# Login user
@app.route("/login", methods=["GET","POST"])
def login():
    session.clear()

    username = request.form.get("username")

    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("error.html", message="must provide username")
        elif not request.form.get("password"):
            return render_template("error.html", message="must provide password")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": username})

        result = rows.fetchone()

        if result == None or not check_password_hash(result[2], request.form.get("password")):
            return render_template("error.html", message="invalid username and/or password")
        session["user_id"] = result[0]
        session["user_name"] = result[1]

        return redirect("/")

    else:
        return render_template("login.html")
        #else:
        #    username = request.form.get("username")
        #    user = db.execute("SELECT * FROM users WHERE username=:username", {"username:username"}).fetchone()
        #    if user is not None:
        #        password = request.form.get("password")
        #        password = user['password']
                # For Verifying
        #        if pbkdf2_sha256.verify(password,Passwd):
        #            session["user_id"] = user ["id"]
        #            session["name"] = user ["full_name"].split(" ")[0]
        #            return render_template("index.html", success_msg = "You are successfully logged in.")
        #        else:
        #            return render_template("login.html", danger_msg = "Incorrect password")
        #    else:
        #        return render_template("login.html", danger_msg = "No user exsist. Please verify your username.")
    #else:
    #    return render_template("login.html")

#user account
@app.route("/account", methods=["GET"])
def account():
    user = db.execute("SELECT * FROM users WHERE id = :user_id", {"user_id": session["user_id"]}).fetchone()
    return render_template("login.html", success_msg = "You've successfully logged out.")







#logout
@app.route("/logout", methods=["GET","POST"])
def logout():
    session.clear()
    return render_template("login.html", success_msg = "You've successfully logged out.")

#book search
@app.route("/search", methods=["GET", "POST"])
def search():
    if not request.args.get("book"):
        return render_template("error.html", message="you must provide a book.")

    query = "%" + request.args.get("book") + "%"

    query = query.title()

    rows = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                        {"query": query})

    if rows.rowcount == 0:
        print("NO book")
        return render_template("error.html", message="we can't find books with that description.")
    else:
        dataRows = rows.fetchall()
        return render_template("search.html", books=dataRows)





#book
@app.route("/book/<isbn>", methods=['GET','POST'])
def book(isbn):
    if request.method == "POST":
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})
        bookId = row.fetchone()
        bookId = bookId[0]
        row1 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                    {"user_id": currentUser,
                     "book_id": bookId})

        # A review already exists
        if row1.rowcount == 1:

            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        rating = int(rating)
        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating) VALUES \
            (:user_id, :book_id, :comment, :rating)",
            {"user_id": currentUser,
            "book_id": bookId,
            "comment": comment,
            "rating": rating})
        db.commit()

        return redirect("/book" + isbn )
    else:
        print("Inside Else for book route")
        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})
        bookInfo = row.fetchall()
        print(bookInfo)


        key = os.getenv("GOODREADS_KEY")
        query = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": key, "isbns": isbn})
        response = query.json()
        response = response['books'][0]
        bookInfo.append(response)

        row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})

        book = row.fetchone()
        book = book[0]

        results = db.execute("SELECT users.username, comment, rating, \
                            to_char(time, 'DD Mon YY - HH24:MI:SS') as time \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.user_id \
                            WHERE book_id = :book \
                            ORDER BY time",
                            {"book": book})
        reviews = results.fetchall()
        return render_template("book.html", bookInfo=bookInfo, reviews=reviews)












@app.route("/review", methods=["GET","POST"])
def review():
    if request.method == "POST":
        global books
        bookid = books['id']
        try:
            user_id = session["user_id"]
            comment = request.form.get("comment")
            res = request.get("https://www.goodreads.com/book/review_counts.json", params = {"key": goodreads_key, "isbns":books['isbn']})
            review = db.execute("SELECT * FROM review WHERE book_id = :book_id", {"book_id": bookid}).fetchall()
            names = []
            for review in reviews:
                userid = review['user_id']
                username = db.execute("SELECT * FROM users WHERE id = :id", {"id": userid}).fetchone()['username']
                names.append(username)
                review1 = db.execute("SELECT *FROM reviews WHERE user_id = :user_id AND book_id = :book_id", {"user_id" : user_id, "book_id": bookid}).fetchone()
            if review1 is None:
                db.execute("INSERT INTO reviews (book_id, user_id, comment, postdate,stars) VALUES (:book_id, :user_id, :comment, :postdate, :stars);", {book_id: bookid,"user_id": user_id, "comment": comment, "postdate": postdate, "stars": stars}).fetchone()
                username1 = db.execute("SELECT * FROM users WHERE id = :id",{"id": session["user_id"]}).fetchone()
                print(username1)
                db.execute("UPDATE users SET review_counts = :count WHERE id = :user_id", {"count": username1['review_count'] + 1,"user_id":user_id})
                db.commit()
                reviews = sb.execute("SELECT * FROM reviews WHERE book_id = :book_id",{"book_id": bookid}).fetchall()
                names= []
                for review in reviews:
                    userid = review['user_id']
                    username = db.execute("SELECT * FROM users WHERE id = :id", {"id": userid}).fetchone()['username']
                    names.append(username)
                return render_template("book.html", book = books, review = res.json()['books'][0], reviews = review, names = names, success_msg="You've review has been saved successfully.")
            else:
                return render_template("book.html", book = books, review = res.json()['books'][0], reviews = reviews, names = names, danger_msg="You can't write another review")
        except keyerror:
            res = request.get("https://www.goodreads.com/book/review_counts.json", params = {"key": goodreads_key, "isbns":books['isbn']})
            reviews = db.execute("SELLECT * FROM reviews WHERE book_id = :book_id",{"book_id": bookid}).fetchall()
            names =[]
            for review in reviews:
                userid = review['user_id']
                username = db.execute("SELECT * FROM users WHERE id = :id", {"id": userid}).fetchone()['username']
                names.append(username)
            return render_template("book.html", book = books, review = res.json()['books'][0], reviews = reviews, names = names, danger_msg = "ERROR! You need to login for reviewing the post.")







@app.route("/api/<isbn>", methods=["GET","POST"])
def api(isbn):

    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.book_id \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})
    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422
    tmp = row.fetchone()
    result = dict(tmp.items())
    result['average_score'] = float('%.2f'%(result['average_score']))

    return jsonify(result)
