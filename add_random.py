import sqlite3
import random

# Sample data
blood_groups = ['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']
names = ['John Smith', 'Emma Wilson', 'Michael Brown', 'Sarah Davis', 'David Lee',
         'Lisa Anderson', 'James Wilson', 'Jennifer Taylor', 'Robert Martin', 'Mary Johnson']
emails = ['john.smith@email.com', 'emma.wilson@email.com', 'michael.brown@email.com',
          'sarah.davis@email.com', 'david.lee@email.com', 'lisa.anderson@email.com',
          'james.wilson@email.com', 'jennifer.taylor@email.com', 'robert.martin@email.com',
          'mary.johnson@email.com']
phones = ['1234567890', '2345678901', '3456789012', '4567890123', '5678901234',
          '6789012345', '7890123456', '8901234567', '9012345678', '0123456789']

# Connect to database
conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Add entries
for i in range(10):
    cur.execute("""
        INSERT INTO blood (type, donorname, donorsex, qty, dweight, donoremail, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        random.choice(blood_groups),
        names[i],
        random.choice(['male', 'female']),
        str(random.randint(1, 3)),
        str(random.randint(50, 100)),
        emails[i],
        phones[i]
    ))

conn.commit()
conn.close()
print("Added 10 random blood donation entries!") 