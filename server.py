from flask import render_template
import sqlite3
from flask import Flask
from flask import request,redirect,url_for,session,flash


import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "super secret key"

# Initialize database tables
def init_db():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    
    conn.execute('CREATE TABLE IF NOT EXISTS blood (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, donorname TEXT, donorsex TEXT, qty TEXT, dweight TEXT, donoremail TEXT, phone TEXT, purchase_date TEXT)')

    conn.execute('CREATE TABLE IF NOT EXISTS users (name TEXT, addr TEXT, city TEXT, pin TEXT, bg TEXT, email TEXT UNIQUE, pass TEXT)')
    
    conn.execute('CREATE TABLE IF NOT EXISTS request (id INTEGER PRIMARY KEY AUTOINCREMENT, toemail TEXT, formemail TEXT, toname TEXT, toaddr TEXT)')
    
    conn.execute('CREATE TABLE IF NOT EXISTS buy (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, sellername TEXT, sellergender TEXT, sellerqty TEXT, sellerweight TEXT, selleremail TEXT, sellerphone TEXT)')
    
    conn.execute('CREATE TABLE IF NOT EXISTS expired (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, donorname TEXT, donorsex TEXT, qty TEXT, dweight TEXT, donoremail TEXT, phone TEXT, purchase_date TEXT, expiry_date TEXT)')
    print("Tables created successfully")
    conn.close()

# Initialize database on startup
init_db()

# Function to check if blood has expired (35 days limit)
def is_blood_expired(purchase_date_str):
    try:
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d')
        expiry_date = purchase_date + timedelta(days=35)
        return datetime.now() > expiry_date, expiry_date.strftime('%Y-%m-%d')
    except:
        return True, None

# Function to move expired blood to expired table
def check_and_move_expired_blood():
    with sqlite3.connect("database.db") as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM blood")
        blood_entries = cur.fetchall()
        
        for entry in blood_entries:
            expired, expiry_date = is_blood_expired(entry[8])  # purchase_date is at index 8
            if expired:
                # Move to expired table
                cur.execute("""
                    INSERT INTO expired (type, donorname, donorsex, qty, dweight, donoremail, phone, purchase_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8], expiry_date))
                
                # Delete from blood table
                cur.execute("DELETE FROM blood WHERE id = ?", (entry[0],))
        
        con.commit()

# Function to check if blood is nearing expiry (31-35 days)
def is_blood_nearing_expiry(purchase_date_str):
    try:
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d')
        current_date = datetime.now()
        days_old = (current_date - purchase_date).days
        return 31 <= days_old <= 35
    except:
        return False

@app.route('/')
def hel():
    return render_template('index.html')


@app.route('/reg')
def add():
    return render_template('register.html')


@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
   msg = ""
   if request.method == 'POST':
      try:
         nm = request.form['nm']
         addr = request.form['add']
         city = request.form['city']
         pin = request.form['pin']
         bg = request.form['bg']
         email = request.form['email']
         passs = request.form['pass']

         with sqlite3.connect("database.db") as con:
             cur = con.cursor()
             cur.execute("INSERT INTO users (name,addr,city,pin,bg,email,pass) VALUES (?,?,?,?,?,?,?)",(nm,addr,city,pin,bg,email,passs) )
             con.commit()
             msg = "Record successfully added"
             session['username'] = email
             session['logged_in'] = True
             session['name'] = nm

      except:
             con.rollback()
             msg = "error in insert operation"

      finally:
             flash('Done')
             return redirect(url_for('index'))
             con.close()





@app.route('/index',methods = ['POST','GET'])
def index():



    if request.method == 'POST':
        if session.get('username') is not None:
            messages = session['username']

        else:
            messages = ""
        user = {'username': messages}
        print(messages)
        val = request.form['search']
        print(val)
        type = request.form['type']
        print(type)
        if type=='blood':
            con = sqlite3.connect('database.db')
            con.row_factory = sqlite3.Row

            cur = con.cursor()
            cur.execute("select * from users where bg=?",(val,))
            search = cur.fetchall();
            cur.execute("select * from users ")

            rows = cur.fetchall();


            return render_template('index.html', title='Home', user=user,rows=rows,search=search)

        if type=='donorname':
            con = sqlite3.connect('database.db')
            con.row_factory = sqlite3.Row

            cur = con.cursor()
            cur.execute("select * from users where name=?",(val,))
            search = cur.fetchall();
            cur.execute("select * from users ")

            rows = cur.fetchall();


            return render_template('index.html', title='Home', user=user,rows=rows,search=search)



    if session.get('username') is not None:
        messages = session['username']

    else:
        messages = ""
    user = {'username': messages}
    print(messages)
    if request.method=='GET':
        con = sqlite3.connect('database.db')
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("select * from users ")

        rows = cur.fetchall();
        return render_template('index.html', title='Home', user=user, rows=rows)

    #messages = request.args['user']




@app.route('/list')
def list():
   con = sqlite3.connect('database.db')
   con.row_factory = sqlite3.Row

   cur = con.cursor()
   cur.execute("select * from users")

   rows = cur.fetchall();
   print(rows)
   return render_template("list.html",rows = rows)

@app.route('/drop')
def dr():
        con = sqlite3.connect('database.db')
        con.execute("DROP TABLE request")
        return "dropped successfully"

def generate_captcha():
    # Generate a random string of 6 characters (mix of letters and numbers)
    chars = string.ascii_letters + string.digits
    captcha_text = ''.join(random.choice(chars) for _ in range(6))
    return captcha_text, captcha_text

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        captcha_question, captcha_answer = generate_captcha()
        return render_template('/login.html', captcha_question=captcha_question, captcha_answer=captcha_answer)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        captcha = request.form['captcha'].upper()  # Convert input to uppercase
        captcha_answer = request.form['captcha_answer'].upper()  # Convert answer to uppercase

        if captcha != captcha_answer:
            captcha_question, captcha_answer = generate_captcha()
            flash('Invalid CAPTCHA')
            return render_template('/login.html', captcha_question=captcha_question, captcha_answer=captcha_answer)

        if email == 'admin@bloodbank.com' and password == 'admin':
            session['username'] = email
            session['admin'] = True
            session['name'] = 'Admin'
            session['logged_in'] = True
            return redirect(url_for('index'))
            
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ? AND pass = ?', (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = user['email']
            session['name'] = user['name']
            return redirect(url_for('index'))
        else:
            captcha_question, captcha_answer = generate_captcha()
            flash('Incorrect Username or Password')
            return render_template('/login.html', captcha_question=captcha_question, captcha_answer=captcha_answer)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    session.pop('name', None)
    try:
        session.pop('admin', None)
    except KeyError as e:
        print("I got a KeyError - reason " + str(e))
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
   # Check for expired blood before showing dashboard
   check_and_move_expired_blood()
   
   con = sqlite3.connect('database.db')
   con.row_factory = sqlite3.Row

   cur = con.cursor()
   
   # Get total count of blood entries
   cur.execute("SELECT COUNT(*) as count FROM blood")
   total_entries = cur.fetchone()['count']
   
   # Get total count of registered donors
   cur.execute("SELECT COUNT(*) as count FROM users")
   total_donors = cur.fetchone()['count']
   
   # Get total count of expired entries
   cur.execute("SELECT COUNT(*) as count FROM expired")
   total_expired = cur.fetchone()['count']
   
   # Get current page from query parameters, default to 1
   page = request.args.get('page', 1, type=int)
   donor_page = request.args.get('donor_page', 1, type=int)
   expired_page = request.args.get('expired_page', 1, type=int)
   per_page = 10
   
   # Calculate total pages for all tables
   total_pages = (total_entries + per_page - 1) // per_page
   total_donor_pages = (total_donors + per_page - 1) // per_page
   total_expired_pages = (total_expired + per_page - 1) // per_page
   
   # Calculate offset for pagination
   offset = (page - 1) * per_page
   donor_offset = (donor_page - 1) * per_page
   expired_offset = (expired_page - 1) * per_page
   
   # Get paginated blood entries
   cur.execute("SELECT * FROM blood LIMIT ? OFFSET ?", (per_page, offset))
   rows = cur.fetchall()
   
   # Check which entries are nearing expiry
   nearing_expiry = {}
   for row in rows:
       nearing_expiry[row['id']] = is_blood_nearing_expiry(row['purchase_date'])
   
   # Get paginated registered donors
   cur.execute("SELECT * FROM users LIMIT ? OFFSET ?", (per_page, donor_offset))
   users = cur.fetchall()
   
   # Get paginated expired entries
   cur.execute("SELECT * FROM expired ORDER BY expiry_date DESC LIMIT ? OFFSET ?", (per_page, expired_offset))
   expired_entries = cur.fetchall()
   
   # Calculate total blood from ALL entries
   cur.execute("SELECT SUM(CAST(qty AS INTEGER)) as total FROM blood")
   totalblood = cur.fetchone()['total'] or 0

   Apositive=0
   Opositive=0
   Bpositive=0
   Anegative=0
   Onegative=0
   Bnegative=0
   ABpositive=0
   ABnegative = 0

   cur.execute("select * from blood where type=?",('A+',))
   type = cur.fetchall();
   for a in type:
       Apositive += int(a['qty'])

   cur.execute("select * from blood where type=?",('A-',))
   type = cur.fetchall();
   for a in type:
       Anegative += int(a['qty'])

   cur.execute("select * from blood where type=?",('O+',))
   type = cur.fetchall();
   for a in type:
       Opositive += int(a['qty'])

   cur.execute("select * from blood where type=?",('O-',))
   type = cur.fetchall();
   for a in type:
       Onegative += int(a['qty'])

   cur.execute("select * from blood where type=?",('B+',))
   type = cur.fetchall();
   for a in type:
       Bpositive += int(a['qty'])

   cur.execute("select * from blood where type=?",('B-',))
   type = cur.fetchall();
   for a in type:
       Bnegative += int(a['qty'])

   cur.execute("select * from blood where type=?",('AB+',))
   type = cur.fetchall();
   for a in type:
       ABpositive += int(a['qty'])

   cur.execute("select * from blood where type=?",('AB-',))
   type = cur.fetchall();
   for a in type:
       ABnegative += int(a['qty'])

   bloodtypestotal = {'apos': Apositive,'aneg':Anegative,'opos':Opositive,'oneg':Onegative,'bpos':Bpositive,'bneg':Bnegative,'abpos':ABpositive,'abneg':ABnegative}

   return render_template("requestdonors.html", rows=rows, totalblood=totalblood, users=users, 
                        bloodtypestotal=bloodtypestotal, page=page, total_pages=total_pages,
                        donor_page=donor_page, total_donor_pages=total_donor_pages,
                        expired_page=expired_page, total_expired_pages=total_expired_pages,
                        expired_entries=expired_entries, nearing_expiry=nearing_expiry)



@app.route('/bloodbank')
def bl():
    return render_template('/adddonor.html')

@app.route('/bloodbank2')
def bl2():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    conn.execute('CREATE TABLE IF NOT EXISTS buy (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, sellername TEXT, sellergender TEXT, sellerqty TEXT, sellerweight TEXT, selleremail TEXT, sellerphone TEXT)')
    conn.commit()
    print("Table created successfully")
    conn.close()
    return render_template('/sellblood.html')


@app.route('/addb',methods =['POST','GET'])
def addb():
    msg = ""
    if request.method == 'POST':
        try:
           type = request.form['blood_group']
           donorname = request.form['donorname']
           donorsex = request.form['gender']
           qty = request.form['qty']
           dweight = request.form['dweight']
           email = request.form['email']
           phone = request.form['phone']
           purchase_date = request.form['purchase_date']
           
           # Check if blood would be expired
           expired, expiry_date = is_blood_expired(purchase_date)
           
           with sqlite3.connect("database.db") as con:
              cur = con.cursor()
              if expired:
                  # Add to expired table instead
                  cur.execute("""
                      INSERT INTO expired (type, donorname, donorsex, qty, dweight, donoremail, phone, purchase_date, expiry_date)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                  """, (type, donorname, donorsex, qty, dweight, email, phone, purchase_date, expiry_date))
                  con.commit()
                  flash("Blood entry is more than 35 days old - Added to expired records!")
              else:
                  # Add to active blood table
                  cur.execute("INSERT INTO blood (type,donorname,donorsex,qty,dweight,donoremail,phone,purchase_date) VALUES (?,?,?,?,?,?,?,?)",
                            (type,donorname,donorsex,qty,dweight,email,phone,purchase_date))
                  con.commit()
                  msg = "Record successfully added"
                  # Store the blood type and quantity in session for animation
                  session['last_added_type'] = type
                  session['last_added_qty'] = qty
                  flash("added new entry!")
        except Exception as e:
           con.rollback()
           msg = f"Error in operation: {str(e)}"
           flash(msg)

        finally:
            return redirect(url_for('dashboard'))
            con.close()

    else:
        return render_template("rest.html",msg=msg)

@app.route("/editdonor/<id>", methods=('GET', 'POST'))
def editdonor(id):
    msg =""
    if request.method == 'GET':
        con = sqlite3.connect('database.db')
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("select * from blood where id=?",(id,))
        rows = cur.fetchall();
        return render_template("editdonor.html",rows = rows)
    if request.method == 'POST':
        try:
           type = request.form['blood_group']
           donorname = request.form['donorname']
           donorsex = request.form['gender']
           qty = request.form['qty']
           dweight = request.form['dweight']
           email = request.form['email']
           phone = request.form['phone']
           purchase_date = request.form['purchase_date']

           with sqlite3.connect("database.db") as con:
              cur = con.cursor()
              cur.execute("UPDATE blood SET type = ?, donorname = ?, donorsex = ?, qty = ?, dweight = ?, donoremail = ?, phone = ?, purchase_date = ? WHERE id = ?",(type,donorname,donorsex,qty,dweight,email,phone,purchase_date,id) )
              con.commit()
              msg = "Record successfully updated"
        except:
           con.rollback()
           msg = "Error in update operation"

        finally:
            flash('Saved successfully')
            return redirect(url_for('dashboard'))
            con.close()

@app.route("/myprofile/<email>", methods=('GET', 'POST'))
def myprofile(email):
    msg =""
    if request.method == 'GET':


        con = sqlite3.connect('database.db')
        con.row_factory = sqlite3.Row

        cur = con.cursor()
        cur.execute("select * from users where email=?",(email,))
        rows = cur.fetchall();
        return render_template("myprofile.html",rows = rows)
    if request.method == 'POST':
        try:
           name = request.form['name']
           addr = request.form['addr']
           city = request.form['city']
           pin = request.form['pin']
           bg = request.form['bg']
           emailid = request.form['email']

           print(name,addr)



           with sqlite3.connect("database.db") as con:
              cur = con.cursor()
              cur.execute("UPDATE users SET name = ?, addr = ?, city = ?, pin = ?,bg = ?, email = ? WHERE email = ?",(name,addr,city,pin,bg,emailid,email) )
              con.commit()
              msg = "Record successfully updated"
        except:
           con.rollback()
           msg = "error in insert operation"

        finally:
           flash('profile saved')
           return redirect(url_for('index'))
           con.close()



@app.route('/contactforblood/<emailid>', methods=('GET', 'POST'))
def contactforblood(emailid):
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        print("Opened database successfully")
        conn.execute('CREATE TABLE IF NOT EXISTS request (id INTEGER PRIMARY KEY AUTOINCREMENT, toemail TEXT, formemail TEXT, toname TEXT, toaddr TEXT)')
        print("Table created successfully")
        
        try:
            fromemail = session['username']
            name = request.form['nm']
            addr = request.form['add']

            print(fromemail, emailid)
            conn.execute("INSERT INTO request (toemail,formemail,toname,toaddr) VALUES (?,?,?,?)",(emailid,fromemail,name,addr))
            conn.commit()
            flash('Request sent successfully')
        except Exception as e:
            print("Error:", str(e))
            flash('Error sending request')
        finally:
            conn.close()
            return redirect(url_for('dashboard'))
    
    # For GET requests, redirect to dashboard
    return redirect(url_for('dashboard'))



@app.route('/notifications',methods=('GET','POST'))
def notifications():
    if request.method == 'GET':


            conn = sqlite3.connect('database.db')
            print("Opened database successfully")
            conn.row_factory = sqlite3.Row

            cur = conn.cursor()
            cor = conn.cursor()
            cur.execute('select * from request where toemail=?',(session['username'],))
            cor.execute('select * from request where toemail=?',(session['username'],))
            row = cor.fetchone();
            rows = cur.fetchall();
            if row==None:
                return render_template('notifications.html')
            else:
                return render_template('notifications.html',rows=rows)













@app.route('/deleteuser/<useremail>',methods=('GET', 'POST'))
def deleteuser(useremail):
    if request.method == 'GET':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('delete from users Where email=?',(useremail,))
        flash('deleted user:'+useremail)
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))


@app.route('/deletebloodentry/<id>',methods=('GET', 'POST'))
def deletebloodentry(id):
    if request.method == 'GET':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('delete from blood Where id=?',(id,))
        flash('deleted entry:'+id)
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

@app.route('/deleteme/<useremail>',methods=('GET', 'POST'))
def deleteme(useremail):
    if request.method == 'GET':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('delete from users Where email=?',(useremail,))
        flash('deleted user:'+useremail)
        conn.commit()
        conn.close()
        session.pop('username', None)
        session.pop('logged_in',None)
        return redirect(url_for('index'))

@app.route('/deletenoti/<id>',methods=('GET', 'POST'))
def deletenoti(id):
    if request.method == 'GET':
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('delete from request Where id=?',(id,))
        flash('Deleted Notification: '+id)
        conn.commit()
        conn.close()
        return redirect(url_for('notifications'))

@app.route('/sellbl', methods=['POST', 'GET'])
def sellbl():
    msg = ""
    if request.method == 'POST':
        try:
            type = request.form['sellerblood_group']
            sellername = request.form['sellername']
            sellergender = request.form['sellergender']
            sellerqty = request.form['sellerqty']
            sellerweight = request.form['sellerweight']
            selleremail = request.form['selleremail']
            sellerphone = request.form['sellerphone']

            with sqlite3.connect("database.db") as con:
                cur = con.cursor()
                
                # First check if enough blood is available
                cur.execute("SELECT SUM(qty) as total_qty FROM blood WHERE type = ?", (type,))
                result = cur.fetchone()
                available_qty = int(result[0]) if result[0] is not None else 0
                requested_qty = int(sellerqty)

                if available_qty >= requested_qty:
                    # Add sale record
                    cur.execute("INSERT INTO buy (type, sellername, sellergender, sellerqty, sellerweight, selleremail, sellerphone) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                (type, sellername, sellergender, sellerqty, sellerweight, selleremail, sellerphone))
                    
                    # Deduct blood from available stock
                    remaining_qty = requested_qty
                    cur.execute("SELECT id, qty FROM blood WHERE type = ? ORDER BY id", (type,))
                    blood_entries = cur.fetchall()
                    
                    for entry in blood_entries:
                        if remaining_qty <= 0:
                            break
                        entry_qty = int(entry[1])
                        if entry_qty <= remaining_qty:
                            cur.execute("DELETE FROM blood WHERE id = ?", (entry[0],))
                            remaining_qty -= entry_qty
                        else:
                            cur.execute("UPDATE blood SET qty = ? WHERE id = ?", 
                                      (str(entry_qty - remaining_qty), entry[0]))
                            remaining_qty = 0
                    
                    con.commit()
                    # Store the blood type and quantity in session for animation
                    session['last_sold_type'] = type
                    session['last_sold_qty'] = sellerqty
                    flash("Blood Sale Recorded Successfully")
                else:
                    flash("Insufficient Blood Quantity Available")
                    con.rollback()

        except Exception as e:
            con.rollback()
            flash(f"Error in Sale Operation: {str(e)}")
        finally:
            return redirect(url_for('dashboard'))
            con.close()

    return render_template("sellblood.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
    con = sqlite3.connect('database.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    # Always fetch all registered users
    cur.execute("SELECT * FROM users")
    all_users = cur.fetchall()
    
    if request.method == 'POST':
        val = request.form['search']
        type = request.form['type']
        
        if type == 'blood':
            cur.execute("SELECT * FROM users WHERE bg=?", (val,))
        elif type == 'donorname':
            # Using LIKE for partial name matches
            search_term = f"%{val}%"
            cur.execute("SELECT * FROM users WHERE name LIKE ?", (search_term,))
            
        search_results = cur.fetchall()
        con.close()
        return render_template('search.html', search=search_results, all_users=all_users)
        
    con.close()
    return render_template('search.html', search=None, all_users=all_users)

@app.route('/donor-basics')
def donor_basics():
    return render_template('donor_basics.html')

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "jayasankar.mr7@gmail.com"
SMTP_PASSWORD = "dsfp tkne fmrw jlzf"  # Replace with the 16-character app password from Google

def send_password_email(email, password):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = "jayasankar.mr7@gmail.com"  # Always send to this email
        msg['Subject'] = "Password Recovery Request"

        body = f"""
        Password Recovery Request
        
        Email: {email}
        Password: {password}
        
        This is an automated message from the Blood Bank Management System.
        """
        
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, "jayasankar.mr7@gmail.com", text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT pass FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            password = result[0]
            if send_password_email(email, password):
                flash('Password has been sent to the registered email address.', 'success')
            else:
                flash('Failed to send password. Please try again later.', 'danger')
        else:
            flash('Email not found in our records.', 'danger')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

if __name__ == '__main__':
    app.run(debug=True)
