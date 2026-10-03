import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pet_adoption.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        role TEXT NOT NULL DEFAULT 'adopter',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Pet Categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pet_categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        icon TEXT
    )
    ''')

    # 3. Pets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pets (
        pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        breed TEXT NOT NULL,
        age TEXT NOT NULL,
        gender TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'Available',
        image_path TEXT,
        adoption_fee REAL NOT NULL DEFAULT 0.0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES pet_categories (category_id) ON DELETE CASCADE
    )
    ''')

    # 4. Medical Records table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER NOT NULL,
        vaccination TEXT NOT NULL,
        health_status TEXT NOT NULL,
        record_date DATE NOT NULL,
        notes TEXT,
        FOREIGN KEY (pet_id) REFERENCES pets (pet_id) ON DELETE CASCADE
    )
    ''')

    # 5. Adoption Requests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS adoption_requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pet_id INTEGER NOT NULL,
        request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL DEFAULT 'Pending',
        message TEXT,
        applicant_income REAL NOT NULL DEFAULT 0.0,
        household_type TEXT,
        has_other_pets INTEGER DEFAULT 0,
        decision_date DATETIME,
        rejection_reason TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        FOREIGN KEY (pet_id) REFERENCES pets (pet_id) ON DELETE CASCADE
    )
    ''')

    # 6. Adoption Request Details table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS adoption_request_details (
        detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        pet_id INTEGER NOT NULL,
        amount REAL NOT NULL DEFAULT 0.0,
        FOREIGN KEY (request_id) REFERENCES adoption_requests (request_id) ON DELETE CASCADE,
        FOREIGN KEY (pet_id) REFERENCES pets (pet_id) ON DELETE CASCADE
    )
    ''')

    # 7. Incomes table (FR-04, SEL-04, SEL-05, SEL-07, BUG-001)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS incomes (
        income_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT NOT NULL,
        amount REAL NOT NULL CHECK(amount >= 0),
        date DATE NOT NULL,
        description TEXT,
        payment_method TEXT DEFAULT 'UPI / NetBanking',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
    )
    ''')

    # 8. Reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pet_id INTEGER NOT NULL,
        rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
        comment TEXT NOT NULL,
        review_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        FOREIGN KEY (pet_id) REFERENCES pets (pet_id) ON DELETE CASCADE
    )
    ''')

    # 9. Defect Logs / STLC tracking table (Supports Section 12 Defect Tracking)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS defect_logs (
        defect_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        module TEXT NOT NULL,
        severity TEXT NOT NULL,
        priority TEXT NOT NULL,
        steps TEXT,
        expected TEXT,
        actual TEXT,
        status TEXT NOT NULL,
        logged_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Seed Users
    # Roles: admin, staff, adopter
    users = [
        ('Anita Kshirsagar (Guide/Admin)', 'admin@petportal.com', generate_password_hash('admin123'), '9876543210', 'Department of Computer Engineering, GP Pune', 'admin'),
        ('NGO Shelter Staff', 'staff@petportal.com', generate_password_hash('staff123'), '9876543211', 'Pune Animal Welfare Sanctuary, Shivajinagar', 'staff'),
        ('Aparna Sunil Bhokare', 'aparna@petportal.com', generate_password_hash('user123'), '9876543212', 'Kothrud, Pune, Maharashtra', 'adopter'),
        ('Anisha Ravindra Todkar', 'anisha@petportal.com', generate_password_hash('user123'), '9876543213', 'Aundh, Pune, Maharashtra', 'adopter'),
        ('Rahul Sharma', 'rahul@gmail.com', generate_password_hash('user123'), '9876543214', 'Viman Nagar, Pune', 'adopter')
    ]
    cursor.executemany('''
    INSERT INTO users (name, email, password_hash, phone, address, role)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', users)

    # Seed Categories
    categories = [
        ('Dogs', 'Loyal, affectionate, and protective canine companions for every home.', 'fa-dog'),
        ('Cats', 'Graceful, independent, and charming feline friends who love cuddles.', 'fa-cat'),
        ('Rabbits', 'Gentle, quiet, and friendly pocket pets ideal for quiet households.', 'fa-carrot'),
        ('Birds', 'Playful and melodic feathered companions with bright personalities.', 'fa-dove')
    ]
    cursor.executemany('''
    INSERT INTO pet_categories (name, description, icon)
    VALUES (?, ?, ?)
    ''', categories)

    # Seed Pets
    pets = [
        (1, 'Buddy', 'Golden Retriever', '4 months', 'Male', 'Extremely friendly, energetic puppy. Fully socialized with children and other animals. Loves outdoor play and fetch.', 'Available', '/static/images/dog1.jpg', 2500.0),
        (2, 'Luna', 'British Shorthair', '1.5 years', 'Female', 'Calm, gentle green-eyed beauty. Loves curling up by sunny windows and playing with soft feather toys.', 'Available', '/static/images/cat1.jpg', 1800.0),
        (3, 'Clover', 'Holland Lop Bunny', '6 months', 'Male', 'Sweet and curious lop-eared bunny. Litter-trained and very social. Enjoys fresh carrots and gentle head scratches.', 'Available', '/static/images/rabbit1.jpg', 800.0),
        (1, 'Rocky', 'German Shepherd', '2 years', 'Male', 'Loyal and highly intelligent. Trained in basic commands, great family protector and outdoor adventure partner.', 'Adopted', '/static/images/dog1.jpg', 3000.0),
        (2, 'Milo', 'Ginger Tabby', '8 months', 'Male', 'Playful, purring ginger kitten with lots of curiosity. Loves lap naps and laser pointers.', 'Pending', '/static/images/cat1.jpg', 1500.0),
        (4, 'Rio', 'Budgerigar Parakeet', '1 year', 'Male', 'Vibrant blue parakeet who chirps happily and mimics short whistles. Very active and healthy.', 'Available', '/static/images/rabbit1.jpg', 600.0)
    ]
    cursor.executemany('''
    INSERT INTO pets (category_id, name, breed, age, gender, description, status, image_path, adoption_fee)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', pets)

    # Seed Medical Records
    records = [
        (1, 'DHPP, Rabies 1st Shot, Dewormed', 'Healthy', '2026-09-15', 'Full puppy checkup completed. Energetic and healthy appetite.'),
        (2, 'FVRCP & Rabies Certified', 'Healthy', '2026-08-20', 'Spayed, up to date on all feline immunizations.'),
        (3, 'Myxomatosis & RHDV Vaccination', 'Healthy', '2026-09-01', 'Teeth checked and clean. Diet of timothy hay recommended.'),
        (4, 'Complete Annual Vaccinations & Microchipped', 'Healthy', '2026-07-10', 'Excellent stamina, joints healthy and certified.'),
        (5, 'Dewormed & FVRCP Initial Shot', 'Under Observation', '2026-09-28', 'Mild ear cleaning done, recovering nicely.')
    ]
    cursor.executemany('''
    INSERT INTO medical_records (pet_id, vaccination, health_status, record_date, notes)
    VALUES (?, ?, ?, ?, ?)
    ''', records)

    # Seed Adoption Requests
    requests = [
        (3, 1, '2026-09-20 10:30:00', 'Approved', 'I have a spacious garden and 5 years experience with golden retrievers. My family is excited to adopt Buddy!', 45000.0, 'Independent Villa with Garden', 0, '2026-09-22 14:00:00', None, 'Home visit verified. Approved for adoption.'),
        (4, 5, '2026-09-25 15:45:00', 'Pending', 'Looking for a gentle indoor kitten companion for my apartment. I work remotely.', 55000.0, 'Apartment 2BHK', 0, None, None, 'Application under shelter review.'),
        (5, 4, '2026-09-10 11:20:00', 'Completed', 'Adopted Rocky for our farmhouse estate. Settling in wonderfully!', 75000.0, 'Farmhouse & Estate', 1, '2026-09-12 16:30:00', None, 'Adoption completed and handed over.')
    ]
    cursor.executemany('''
    INSERT INTO adoption_requests (user_id, pet_id, request_date, status, message, applicant_income, household_type, has_other_pets, decision_date, rejection_reason, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', requests)

    # Seed Adoption Request Details
    details = [
        (1, 1, 2500.0),
        (2, 5, 1500.0),
        (3, 4, 3000.0)
    ]
    cursor.executemany('''
    INSERT INTO adoption_request_details (request_id, pet_id, amount)
    VALUES (?, ?, ?)
    ''', details)

    # Seed Incomes (FR-04, SEL-04, SEL-05, SEL-07)
    incomes = [
        (3, 'Adoption Fee', 2500.0, '2026-09-22', 'Adoption fee for Buddy (Golden Retriever) - Request #1', 'UPI / NetBanking'),
        (5, 'Adoption Fee', 3000.0, '2026-09-12', 'Adoption fee for Rocky (German Shepherd) - Request #3', 'Online / Card'),
        (1, 'Donation', 15000.0, '2026-09-01', 'Rotary Club of Pune Animal Welfare Grant', 'Bank Transfer'),
        (2, 'Donation', 5000.0, '2026-09-15', 'Community Pet Nutrition & Care Donation', 'UPI'),
        (4, 'Sponsorship', 3500.0, '2026-09-28', 'Veterinary Checkup & Vaccine Sponsorship', 'UPI')
    ]
    cursor.executemany('''
    INSERT INTO incomes (user_id, category, amount, date, description, payment_method)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', incomes)

    # Seed Reviews
    reviews = [
        (3, 1, 5, 'Adopting Buddy was the smoothest experience! The health records and transparency from the portal were fantastic.', '2026-09-25 18:00:00'),
        (5, 4, 5, 'Rocky is the sweetest, well-trained dog. Thank you to GP Pune Pet Adoption Portal for making this possible!', '2026-09-18 19:30:00'),
        (4, 2, 4, 'Visited Luna at the shelter; she is so calm and affectionate. Beautiful facility.', '2026-09-29 11:15:00')
    ]
    cursor.executemany('''
    INSERT INTO reviews (user_id, pet_id, rating, comment, review_date)
    VALUES (?, ?, ?, ?, ?)
    ''', reviews)

    # Seed Defect Report BUG-001 (Matches Section 12.3 of Project Report)
    defect = (
        'BUG-001',
        'Negative adoption request amount accepted',
        'Adoption Request Management',
        'High',
        'High',
        'Enter negative amount and click Save in income / adoption fee form',
        'System rejects negative amount with clear validation message',
        'Record was accepted before bug fix; Fixed in v1.1 with backend and frontend validation constraint',
        'Resolved',
        '2026-09-24 10:00:00'
    )
    cursor.execute('''
    INSERT INTO defect_logs (defect_id, title, module, severity, priority, steps, expected, actual, status, logged_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', defect)

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully!")

if __name__ == '__main__':
    init_db()
    seed_db()
