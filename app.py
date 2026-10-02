import os
from datetime import date, timedelta
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///library.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(30), unique=True, nullable=False)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    book = db.relationship("Book")
    member = db.relationship("Member")

    @property
    def status(self):
        if self.return_date:
            return "Returned"
        return "Overdue" if self.due_date < date.today() else "Issued"

    @property
    def fine(self):
        end = self.return_date or date.today()
        days_late = max((end - self.due_date).days, 0)
        return Decimal(days_late * 5)

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        books=Book.query.count(),
        available=sum(b.available_copies for b in Book.query.all()),
        members=Member.query.count(),
        active=Loan.query.filter_by(return_date=None).count(),
        overdue=sum(1 for l in Loan.query.filter_by(return_date=None).all()
                    if l.due_date < date.today())
    )

@app.route("/books")
def books():
    search = request.args.get("q", "").strip()
    query = Book.query
    if search:
        query = query.filter(
            db.or_(Book.title.ilike(f"%{search}%"),
                   Book.author.ilike(f"%{search}%"),
                   Book.isbn.ilike(f"%{search}%"))
        )
    return render_template("books.html", books=query.order_by(Book.title).all(), q=search)

@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        try:
            copies = int(request.form["total_copies"])
            if copies < 1:
                raise ValueError
            book = Book(title=request.form["title"].strip(),
                        author=request.form["author"].strip(),
                        isbn=request.form["isbn"].strip(),
                        total_copies=copies, available_copies=copies)
            db.session.add(book)
            db.session.commit()
            flash("Book added successfully.", "success")
            return redirect(url_for("books"))
        except (ValueError, KeyError):
            db.session.rollback()
            flash("Enter a valid copy count (at least 1).", "danger")
        except Exception:
            db.session.rollback()
            flash("Could not add book. Check that the ISBN is unique.", "danger")
    return render_template("book_form.html", book=None)

@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if Loan.query.filter_by(book_id=book.id, return_date=None).first():
        flash("Cannot delete a book with an active loan.", "danger")
    else:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted.", "success")
    return redirect(url_for("books"))

@app.route("/members")
def members():
    return render_template("members.html", members=Member.query.order_by(Member.name).all())

@app.route("/members/add", methods=["GET", "POST"])
def add_member():
    if request.method == "POST":
        member = Member(name=request.form["name"].strip(),
                        email=request.form["email"].strip().lower())
        db.session.add(member)
        try:
            db.session.commit()
            flash("Member registered.", "success")
            return redirect(url_for("members"))
        except Exception:
            db.session.rollback()
            flash("Could not add member. Email may already exist.", "danger")
    return render_template("member_form.html")

@app.route("/loans")
def loans():
    return render_template("loans.html", loans=Loan.query.order_by(Loan.id.desc()).all())

@app.route("/loans/issue", methods=["GET", "POST"])
def issue_book():
    if request.method == "POST":
        book = db.session.get(Book, int(request.form["book_id"]))
        member = db.session.get(Member, int(request.form["member_id"]))
        if not book or not member:
            flash("Select a valid book and member.", "danger")
        elif book.available_copies < 1:
            flash("No copies are currently available.", "danger")
        else:
            loan = Loan(book=book, member=member,
                        due_date=date.today() + timedelta(days=14))
            book.available_copies -= 1
            db.session.add(loan)
            db.session.commit()
            flash("Book issued. Due in 14 days.", "success")
            return redirect(url_for("loans"))
    return render_template("issue_form.html", books=Book.query.filter(Book.available_copies > 0).all(),
                           members=Member.query.order_by(Member.name).all())

@app.route("/loans/<int:loan_id>/return", methods=["POST"])
def return_book(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.return_date:
        flash("This book has already been returned.", "warning")
    else:
        loan.return_date = date.today()
        loan.book.available_copies += 1
        db.session.commit()
        flash(f"Book returned. Fine due: ₹{loan.fine:.2f}", "success")
    return redirect(url_for("loans"))

@app.route("/reports")
def reports():
    active = Loan.query.filter_by(return_date=None).all()
    overdue = [loan for loan in active if loan.due_date < date.today()]
    return render_template("reports.html", overdue=overdue,
                           total_fines=sum((loan.fine for loan in Loan.query.all()), Decimal("0")))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
