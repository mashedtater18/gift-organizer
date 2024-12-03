from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_session import Session #import Flask-Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, usd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123'


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False  # Session will expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"  # Store session data on the server's filesystem
app.secret_key = 'supersecretkey123'  # Required to encrypt session data
Session(app)  # Initialize session handling

# Connect to SQLite database (creates the file if it doesn't exist)
db = SQL("sqlite:///gift_organizer.db")
@app.route('/')
@login_required
def index():
        
    user_id = session["user_id"]

    # Execute the query to fetch the username based on the user_id
    result = db.execute("SELECT username FROM users WHERE id = ?", user_id)

    # Check if the result contains a username
    if result:
        username = result[0]["username"]  # Retrieve the username from the result
    else:
        username = None  # If no result, set username to None (handle this appropriately in your template)

    # Define the SQL query using triple quotes for readability
    query = """
    SELECT 
        gifts.id, 
        gifts.gift_name, 
        gifts.amount_spent, 
        gifts.status, 
        recipients.name AS recipient_name,
        recipients.id AS recipient_id
    FROM 
        gifts 
    JOIN 
        recipients 
    ON 
        gifts.recipient_id = recipients.id 
    WHERE 
        gifts.user_id = ?;
    """

    # Execute the query and pass the user_id parameter
    gifts = db.execute(query, user_id)

    # The results (rows) can now be used in your application, e.g., to pass to a template
    return render_template("index.html", gifts=gifts, username=username)


@app.route('/add_gift', methods=['GET', 'POST'])
@login_required
def add_gift():

    if request.method == 'POST':

        # get user inputs
        recipient_id = request.form.get("recipient_id")  # Dropdown selection gives recipient_id
        gift_name = request.form.get("gift_name")
        amount_spent = int(request.form.get("amount_spent"))
        status = request.form.get("status")

        try:
            # check for blank fields
            if not recipient_id or not gift_name or not amount_spent or not status:
                return "Fields cannot be blank!"   
            
            #check for correct amount spent input (i.e. must be non-negative integer)
            amount_spent = int(amount_spent)
            if amount_spent < 0:
                raise ValueError("Amount spent must be nonnegative.")

            # Insert the gift into the database
            db.execute("INSERT INTO gifts (recipient_id, gift_name, amount_spent, status, user_id) VALUES (?, ?, ?, ?, ?)",
            recipient_id, gift_name, amount_spent, status, session["user_id"])

            return redirect("/") #check this - do we want redirect to home? 
        
        except ValueError as e:
            # Handle the error (e.g., show an error message)
            return render_template("add_gift.html", error=str(e))      
        
    else:
        # For GET requests, fetch existing recipients
        recipients = db.execute("SELECT id, name FROM recipients WHERE user_id = ?", session["user_id"])
        return render_template("add_gift.html", recipients=recipients)
    
@app.route("/add_recipient", methods=["GET", "POST"])
@login_required
def add_recipient():
    if request.method == "POST":
        
        # Get the user inputs
        recipient_name = request.form.get("recipient_name")
        budget = request.form.get("budget")
        
        # option to add a gift

        # Insert the recipient into the database
        db.execute(
            "INSERT INTO recipients (name, budget, user_id) VALUES (?, ?, ?)",
            recipient_name, budget, session["user_id"]
        )
        return redirect("/add_gift")  # Redirect back to add gift page
    
    return render_template("add_recipient.html")

@app.route("/delete_gift", methods=["POST"])
@login_required
def delete_gift():

    # get gift id from form
    gift_id = request.form.get("gift_id")

    # check for errors - is gift id valid?
    if not gift_id:
        return ("Gift ID is required", 400) #bad request
    
    # delete gift from db
    db.execute("DELETE FROM gifts WHERE id = ?", gift_id)

    #redirect back to summary page (index)
    return redirect("/")


@app.route("/edit_gift", methods=["POST"])
def edit_gift():
    # Get the JSON data sent from the front-end
    data = request.get_json()
    gift_id = data.get("id")
    gift_name = data.get("gift_name")
    amount_spent = data.get("amount_spent")
    status = data.get("status")

    # Ensure all required data is present
    if not all([gift_id, gift_name, amount_spent, status]):
        return jsonify({"error": "Missing data"}), 400

    # Update the gift in the database
    try:
        db.execute(
            "UPDATE gifts SET gift_name = ?, amount_spent = ?, status = ? WHERE id = ?",
            gift_name,
            float(amount_spent),
            status,
            gift_id
        )
        return jsonify({"message": "Gift updated successfully"}), 200
    except Exception as e:
        print("Error updating gift:", e)
        return jsonify({"error": "Database error"}), 500


@app.route("/recipient_summary/<int:recipient_id>", methods=['GET', 'POST'])
def recipient_summary(recipient_id):

    user_id = session["user_id"]  # Ensure the user_id is obtained correctly

    # Fetch recipient data
    query_recipient = """
    SELECT 
        id, name, budget 
    FROM 
        recipients 
    WHERE 
        id = ? AND user_id = ?;
    """
    recipient = db.execute(query_recipient, recipient_id, user_id)
    
     # Check if recipient is None or if no data is returned
    if not recipient:
        return "Recipient not found", 404
    
    print("Recipient found:", recipient)

    
    # Extract the first row of the result (recipient[0])
    # recipient = recipient[0]  # Now recipient is a dictionary with the data
    # recipient[0] should contain the first (and possibly only) recipient
    recipient = recipient[0]  # This is a dictionary
    recipient_name = recipient["name"]
    overall_budget = recipient["budget"]
    recipient_id = recipient["id"]  


    # Fetch gifts for this recipient
    query_gifts = """
    SELECT 
        id, gift_name, amount_spent, status 
    FROM 
        gifts 
    WHERE 
        recipient_id = ? AND user_id = ?;
    """
    gifts = db.execute(query_gifts, recipient_id, user_id)

    # Calculate total spent and remaining budget
    total_spent = sum(gift['amount_spent'] for gift in gifts)
    remaining_budget = overall_budget - total_spent

    # Pass data to the template
    # #return render_template(
    #     "recipient_summary.html", 
    #     recipient=recipient, 
    #     gifts=gifts, 
    #     budget=overall_budget, 
    #     total_spent=total_spent, 
    #     remaining_budget=remaining_budget)

    if request.method == "POST":

         # Debugging: Check if flash is triggered
        print("POST request received - flashing message")

        # Flash a success message
        flash("Changes saved!", "primary")
        
        # Redirect to the same page to avoid resubmission
        return redirect(url_for("recipient_summary", recipient_id=recipient_id))

    # Render the recipient summary page with budget data
    return render_template(
        "recipient_summary.html",
        recipient_name=recipient_name,
        gifts=gifts,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        budget=overall_budget,
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return ("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return ("must provide password")
        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return ("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register user"""

    # handle form transmission - get username, password, pass conf
    if request.method == "POST":

        # handle form submission
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username not blank
        if not username or not password or not confirmation:
            return ("All fields must be filled out")

        # Ensure passwords match
        if password != confirmation:
            return ("passwords do not match")

        # generate password hash
        hash = generate_password_hash(request.form.get("password"))

        # check to make sure username isn't already taken
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) == 0:
            # Proceed with adding the user
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)

            # After inserting the new user
            user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
            session["user_id"] = user_id

        else:
            return ("username already taken")

        return redirect("/")

    else:
        return render_template("register.html")


@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    return redirect("/login")  # Redirect to the login page


# sample code below
# route for displaying gifts for 1 recipient as well as budget status

@app.route("/recipient/<string:recipient_name>")
@login_required
def get_recipient_data(recipient_name):
    # Query the gifts and budget data for this recipient - recipient summary
    rows = db.execute("""
        SELECT 
            recipient,
            gift,
            price,
            status,
            SUM(price) OVER (PARTITION BY recipient) AS total_spent,
            budget - SUM(price) OVER (PARTITION BY recipient) AS remaining_budget
        FROM gifts
        WHERE recipient = :recipient_name
    """, recipient_name=recipient_name)

    # If the recipient doesn't exist, return a 404 error
    if not rows:
        return "Recipient not found", 404


    # Render the page with recipient details
    return render_template("recipient.html", rows=rows, recipient_name=recipient_name)

@app.route('/save_changes/<gift_id>', methods=["POST"])
def save_changes(gift_id):
    # Handle saving the changes (update the gift in the database)
    # Example: update gift details based on the form data
    # (might need to put this back?) updated_gift_name = request.form['gift_name']  # Example field from the form

    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # Fetch the gift using gift_id and validate user_id
    query = "SELECT * FROM gifts WHERE id = ? AND user_id = ?"
    gift = db.execute(query, gift_id, user_id)

    if not gift:
        return "Gift not found or access denied", 404

    # Perform the save operation (if needed, update database with new values)
    # For example, if you're editing the gift_name or amount_spent:
    updated_name = request.form.get("gift_name")  # Replace 'gift_name' with your field name
    updated_amount = request.form.get("amount_spent")

    update_query = """
        UPDATE gifts
        SET gift_name = ?, amount_spent = ?
        WHERE id = ? AND user_id = ?
    """
    db.execute(update_query, updated_name, updated_amount, gift_id, user_id)

    # Flash success message
    flash("Changes saved!", "primary")

    # Redirect back to the recipient summary page
    return redirect(url_for("recipient_summary", recipient_id=gift["recipient_id"]))


@app.route("/delete_recipient", methods=["POST"])
def delete_recipient():
    # Your delete logic here...
    flash("Recipient deleted successfully!", "danger")  # Flash a danger message
    return redirect(url_for("recipient_summary"))

@app.route("/update_budget", methods=["POST"])
def update_budget():

    recipient_id = request.form.get('recipient_id') #get recipient id
    new_budget = request.form.get('budget') #get new budget value

    # Validate input
    if not new_budget or not recipient_id:
        return "Invalid input", 400
    
    try:
        # Update the recipient's budget in the database
        db.execute("UPDATE recipients SET budget = ? WHERE id = ?", new_budget, recipient_id)
        flash("Budget updated successfully!", "success")
        return redirect(f"/recipient_summary/{recipient_id}")
    
    except Exception as e:
        print(f"Error updating budget: {e}")
        flash("An error occurred while updating the budget.", "error")
        return "An error occurred", 500

if __name__ == "__main__":
    app.run(debug=True)

