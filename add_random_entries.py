import sqlite3
import random
from datetime import datetime, timedelta
import string

def generate_random_name():
    first_names = ['John', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'James', 'Maria', 'Robert', 'Anna',
                  'William', 'Jennifer', 'Thomas', 'Emily', 'Daniel', 'Sophie', 'Christopher', 'Rachel', 'Kevin', 'Michelle']
    last_names = ['Smith', 'Johnson', 'Brown', 'Wilson', 'Lee', 'Chen', 'Taylor', 'Garcia', 'Kim', 'White',
                 'Anderson', 'Lopez', 'Turner', 'Davis', 'Patel', 'Martin', 'Wong', 'Green', 'Lee', 'Rodriguez']
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_random_email(name, counter):
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
    name = name.lower().replace(' ', '.')
    return f"{name}{counter}@{random.choice(domains)}"

def generate_random_phone():
    return ''.join(random.choices(string.digits, k=10))

def generate_random_date(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def generate_random_address():
    streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Pine Rd', 'Cedar Ln', 'Elm St', 'Birch Blvd', 'Willow Dr']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego']
    return f"{random.randint(1, 999)} {random.choice(streets)}, {random.choice(cities)}"

def generate_random_pin():
    return ''.join(random.choices(string.digits, k=6))

def generate_random_blood_type():
    blood_types = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
    return random.choice(blood_types)

def generate_random_weight():
    return random.randint(50, 100)

def generate_random_quantity():
    return random.randint(1, 3)

def add_random_entries():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Generate 100 random entries
    for i in range(100):
        # Generate random data
        name = generate_random_name()
        email = generate_random_email(name, i)  # Add counter to ensure unique emails
        blood_type = generate_random_blood_type()
        weight = generate_random_weight()
        quantity = generate_random_quantity()
        phone = generate_random_phone()
        address = generate_random_address()
        city = address.split(', ')[1]
        pin = generate_random_pin()
        gender = random.choice(['Male', 'Female'])
        
        # Generate random purchase date between 1 and 40 days ago
        end_date = datetime.now()
        start_date = end_date - timedelta(days=40)
        purchase_date = generate_random_date(start_date, end_date).strftime('%Y-%m-%d')
        
        try:
            # Add to users table
            cursor.execute("""
                INSERT INTO users (name, addr, city, pin, bg, email, pass)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, address, city, pin, blood_type, email, 'pass123'))
            
            # Add to blood table
            cursor.execute("""
                INSERT INTO blood (type, donorname, donorsex, qty, dweight, donoremail, phone, purchase_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (blood_type, name, gender, quantity, weight, email, phone, purchase_date))
            
            # Check if blood should be expired (more than 35 days old)
            purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d')
            if (datetime.now() - purchase_date_obj).days > 35:
                expiry_date = (purchase_date_obj + timedelta(days=35)).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO expired (type, donorname, donorsex, qty, dweight, donoremail, phone, purchase_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (blood_type, name, gender, quantity, weight, email, phone, purchase_date, expiry_date))
        except sqlite3.IntegrityError:
            print(f"Skipping duplicate entry for {email}")
            continue
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_random_entries()
    print("Successfully added random entries to the database!") 