import os
import io
import csv
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, Response, make_response
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np

# Matplotlib headless backend for server-side chart rendering
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import database

app = Flask(__name__)
app.secret_key = 'gp-pune-pet-adoption-portal-super-secret-key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure database is initialized
database.init_db()
database.seed_db()

# --- Auth Helpers ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def staff_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') not in ['admin', 'staff']:
            flash('Access restricted to staff or administrators.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            flash('Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_data():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pet_categories")
    categories = cursor.fetchall()
    conn.close()
    return {
        'nav_categories': categories,
        'current_year': datetime.now().year,
        'session_user': session.get('name'),
        'session_role': session.get('role')
    }

# ==========================================
# 1. PUBLIC ROUTES (Home, Pets, Details)
# ==========================================

@app.route('/')
def index():
    conn = database.get_db()
    cursor = conn.cursor()

    # Featured pets (limit 6)
    cursor.execute('''
        SELECT p.*, c.name as category_name
        FROM pets p
        JOIN pet_categories c ON p.category_id = c.category_id
        ORDER BY p.pet_id DESC LIMIT 6
    ''')
    featured_pets = cursor.fetchall()

    # Overview statistics
    cursor.execute("SELECT COUNT(*) FROM pets WHERE status = 'Available'")
    available_pets_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pets WHERE status = 'Adopted'")
    adopted_pets_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoption_requests")
    total_requests_count = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes")
    total_funds = cursor.fetchone()[0]

    # Recent reviews
    cursor.execute('''
        SELECT r.*, u.name as user_name, p.name as pet_name
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        JOIN pets p ON r.pet_id = p.pet_id
        ORDER BY r.review_id DESC LIMIT 3
    ''')
    recent_reviews = cursor.fetchall()

    conn.close()
    return render_template(
        'index.html',
        featured_pets=featured_pets,
        available_count=available_pets_count,
        adopted_count=adopted_pets_count,
        requests_count=total_requests_count,
        funds_count=total_funds,
        reviews=recent_reviews
    )

@app.route('/pets')
def pets():
    conn = database.get_db()
    cursor = conn.cursor()

    # Filter params
    category_id = request.args.get('category', default='', type=str)
    gender = request.args.get('gender', default='', type=str)
    status = request.args.get('status', default='', type=str)
    search_query = request.args.get('q', default='', type=str).strip()

    query = '''
        SELECT p.*, c.name as category_name
        FROM pets p
        JOIN pet_categories c ON p.category_id = c.category_id
        WHERE 1=1
    '''
    params = []

    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if gender:
        query += " AND p.gender = ?"
        params.append(gender)
    if status:
        query += " AND p.status = ?"
        params.append(status)
    if search_query:
        query += " AND (p.name LIKE ? OR p.breed LIKE ? OR p.description LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term])

    query += " ORDER BY p.pet_id DESC"
    cursor.execute(query, params)
    pet_list = cursor.fetchall()

    cursor.execute("SELECT * FROM pet_categories")
    categories = cursor.fetchall()

    conn.close()
    return render_template(
        'pets.html',
        pets=pet_list,
        categories=categories,
        selected_category=category_id,
        selected_gender=gender,
        selected_status=status,
        search_query=search_query
    )

@app.route('/pet/<int:pet_id>')
def pet_detail(pet_id):
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.*, c.name as category_name
        FROM pets p
        JOIN pet_categories c ON p.category_id = c.category_id
        WHERE p.pet_id = ?
    ''', (pet_id,))
    pet = cursor.fetchone()

    if not pet:
        conn.close()
        flash('Pet not found.', 'danger')
        return redirect(url_for('pets'))

    # Medical records
    cursor.execute('''
        SELECT * FROM medical_records
        WHERE pet_id = ?
        ORDER BY record_date DESC
    ''', (pet_id,))
    medical_records = cursor.fetchall()

    # Reviews
    cursor.execute('''
        SELECT r.*, u.name as user_name
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.pet_id = ?
        ORDER BY r.review_id DESC
    ''', (pet_id,))
    reviews = cursor.fetchall()

    # Check if current user already submitted a pending request for this pet
    user_has_requested = False
    if 'user_id' in session:
        cursor.execute('''
            SELECT COUNT(*) FROM adoption_requests
            WHERE user_id = ? AND pet_id = ? AND status IN ('Pending', 'Approved')
        ''', (session['user_id'], pet_id))
        user_has_requested = cursor.fetchone()[0] > 0

    conn.close()
    return render_template(
        'pet_detail.html',
        pet=pet,
        medical_records=medical_records,
        reviews=reviews,
        user_has_requested=user_has_requested
    )

# ==========================================
# 2. ADOPTION REQUESTS (FR-03, FR-05, SEL-06, BUG-001)
# ==========================================

@app.route('/adopt/<int:pet_id>', methods=['GET', 'POST'])
@login_required
def submit_adoption_request(pet_id):
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pets WHERE pet_id = ?", (pet_id,))
    pet = cursor.fetchone()
    if not pet:
        conn.close()
        flash('Pet not found.', 'danger')
        return redirect(url_for('pets'))

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        income_str = request.form.get('applicant_income', '').strip()
        household_type = request.form.get('household_type', '').strip()
        has_other_pets = 1 if request.form.get('has_other_pets') == '1' else 0

        # Strict validation
        if not message:
            flash('Please provide an adoption motivation message.', 'danger')
            conn.close()
            return render_template('adopt_form.html', pet=pet)

        try:
            applicant_income = float(income_str) if income_str else 0.0
        except ValueError:
            flash('Applicant monthly income must be a valid numeric value.', 'danger')
            conn.close()
            return render_template('adopt_form.html', pet=pet)

        # Defect Prevention / Validation: Check for negative income/amount (BUG-001 / SEL-07)
        if applicant_income < 0:
            flash('Income / amount cannot be negative. Please enter a valid positive value.', 'danger')
            conn.close()
            return render_template('adopt_form.html', pet=pet)

        # Insert adoption request
        cursor.execute('''
            INSERT INTO adoption_requests (user_id, pet_id, message, applicant_income, household_type, has_other_pets, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (session['user_id'], pet_id, message, applicant_income, household_type, has_other_pets))
        request_id = cursor.lastrowid

        # Insert into adoption_request_details table
        cursor.execute('''
            INSERT INTO adoption_request_details (request_id, pet_id, amount)
            VALUES (?, ?, ?)
        ''', (request_id, pet_id, pet['adoption_fee']))

        conn.commit()
        conn.close()
        flash('Your adoption request has been submitted successfully! You can track its status in your dashboard.', 'success')
        return redirect(url_for('my_requests'))

    conn.close()
    return render_template('adopt_form.html', pet=pet)

@app.route('/my-requests')
@login_required
def my_requests():
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.*, p.name as pet_name, p.breed, p.image_path, p.adoption_fee, c.name as category_name
        FROM adoption_requests r
        JOIN pets p ON r.pet_id = p.pet_id
        JOIN pet_categories c ON p.category_id = c.category_id
        WHERE r.user_id = ?
        ORDER BY r.request_id DESC
    ''', (session['user_id'],))
    requests_list = cursor.fetchall()

    conn.close()
    return render_template('my_requests.html', requests=requests_list)

@app.route('/requests')
@staff_or_admin_required
def manage_requests():
    conn = database.get_db()
    cursor = conn.cursor()

    status_filter = request.args.get('status', '')
    query = '''
        SELECT r.*, u.name as user_name, u.email as user_email, u.phone as user_phone,
               p.name as pet_name, p.breed as pet_breed, p.adoption_fee, c.name as category_name
        FROM adoption_requests r
        JOIN users u ON r.user_id = u.user_id
        JOIN pets p ON r.pet_id = p.pet_id
        JOIN pet_categories c ON p.category_id = c.category_id
    '''
    params = []
    if status_filter:
        query += " WHERE r.status = ?"
        params.append(status_filter)

    query += " ORDER BY r.request_id DESC"
    cursor.execute(query, params)
    all_requests = cursor.fetchall()

    conn.close()
    return render_template('manage_requests.html', requests=all_requests, status_filter=status_filter)

@app.route('/requests/update-status/<int:request_id>', methods=['POST'])
@staff_or_admin_required
def update_request_status(request_id):
    new_status = request.form.get('status')
    notes = request.form.get('notes', '').strip()
    rejection_reason = request.form.get('rejection_reason', '').strip()

    if new_status not in ['Pending', 'Approved', 'Rejected', 'Completed']:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('manage_requests'))

    conn = database.get_db()
    cursor = conn.cursor()

    # Get pet_id and fee
    cursor.execute("SELECT pet_id, user_id FROM adoption_requests WHERE request_id = ?", (request_id,))
    req = cursor.fetchone()
    if not req:
        conn.close()
        flash('Request not found.', 'danger')
        return redirect(url_for('manage_requests'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE adoption_requests
        SET status = ?, notes = ?, rejection_reason = ?, decision_date = ?
        WHERE request_id = ?
    ''', (new_status, notes, rejection_reason if new_status == 'Rejected' else None, now, request_id))

    # If completed, update pet status to 'Adopted' and optionally record income if not already recorded
    if new_status == 'Completed':
        cursor.execute("UPDATE pets SET status = 'Adopted' WHERE pet_id = ?", (req['pet_id'],))
        # Get pet info
        cursor.execute("SELECT name, adoption_fee FROM pets WHERE pet_id = ?", (req['pet_id'],))
        pet_info = cursor.fetchone()
        if pet_info and pet_info['adoption_fee'] > 0:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO incomes (user_id, category, amount, date, description, payment_method)
                VALUES (?, 'Adoption Fee', ?, ?, ?, 'Adoption Confirmation')
            ''', (req['user_id'], pet_info['adoption_fee'], today, f"Adoption fee for {pet_info['name']} (Request #{request_id})"))
    elif new_status == 'Approved':
        cursor.execute("UPDATE pets SET status = 'Pending' WHERE pet_id = ?", (req['pet_id'],))
    elif new_status == 'Rejected':
        cursor.execute("UPDATE pets SET status = 'Available' WHERE pet_id = ?", (req['pet_id'],))

    conn.commit()
    conn.close()
    flash(f'Adoption request #{request_id} has been marked as {new_status}.', 'success')
    return redirect(url_for('manage_requests'))

# ==========================================
# 3. FINANCIAL / INCOME MANAGEMENT (FR-04, SEL-04, SEL-05, SEL-07, BUG-001)
# ==========================================

@app.route('/income', methods=['GET', 'POST'])
@login_required
def income():
    conn = database.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Add income entry
        category = request.form.get('category', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        date = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()
        payment_method = request.form.get('payment_method', 'UPI / Online').strip()

        # SEL-04: Empty income form validation
        if not category or not amount_raw or not date:
            flash('All required fields (Category, Amount, Date) must be filled.', 'danger')
            return redirect(url_for('income'))

        try:
            amount = float(amount_raw)
        except ValueError:
            flash('Amount must be a valid numeric number.', 'danger')
            return redirect(url_for('income'))

        # SEL-07 & BUG-001 Fix: Reject negative amount
        if amount < 0:
            flash('Amount must be greater than or equal to 0. Negative amounts are not allowed.', 'danger')
            return redirect(url_for('income'))

        cursor.execute('''
            INSERT INTO incomes (user_id, category, amount, date, description, payment_method)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session.get('user_id'), category, amount, date, description, payment_method))
        conn.commit()

        # SEL-05: Record saved
        flash(f'Income record of ₹{amount:,.2f} ({category}) added successfully!', 'success')
        return redirect(url_for('income'))

    # Calculate financial metrics (FR-04)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes")
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoption_requests")
    total_adoption_requests = cursor.fetchone()[0]

    # Calculate balance (Total income minus operational expenses; standard academic model)
    # If expenses exist or calculated:
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes WHERE category = 'Adoption Fee'")
    total_adoption_fees = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes WHERE category = 'Donation'")
    total_donations = cursor.fetchone()[0]

    # For balance calculation: Balance = Total Income (since all income is collected revenue)
    balance = total_income

    # Fetch recent income records
    cursor.execute('''
        SELECT i.*, u.name as recorder_name
        FROM incomes i
        LEFT JOIN users u ON i.user_id = u.user_id
        ORDER BY i.date DESC, i.income_id DESC
    ''')
    incomes_list = cursor.fetchall()

    conn.close()
    return render_template(
        'income.html',
        total_income=total_income,
        total_requests=total_adoption_requests,
        balance=balance,
        total_fees=total_adoption_fees,
        total_donations=total_donations,
        incomes=incomes_list,
        today_date=datetime.now().strftime('%Y-%m-%d')
    )

@app.route('/income/delete/<int:income_id>', methods=['POST'])
@staff_or_admin_required
def delete_income(income_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incomes WHERE income_id = ?", (income_id,))
    conn.commit()
    conn.close()
    flash('Income entry deleted successfully.', 'info')
    return redirect(url_for('income'))

# ==========================================
# 4. REPORTS, GRAPHS & EXPORT (FR-06, FR-07, SEL-08)
# ==========================================

@app.route('/reports')
@login_required
def reports():
    conn = database.get_db()

    # Use Pandas for data manipulation (As specified in Section 2.3)
    try:
        pets_df = pd.read_sql_query('''
            SELECT p.pet_id, p.name, p.status, p.adoption_fee, c.name as category
            FROM pets p
            JOIN pet_categories c ON p.category_id = c.category_id
        ''', conn)
    except Exception:
        pets_df = pd.DataFrame()

    try:
        req_df = pd.read_sql_query('''
            SELECT request_id, status, request_date, applicant_income
            FROM adoption_requests
        ''', conn)
    except Exception:
        req_df = pd.DataFrame()

    try:
        inc_df = pd.read_sql_query('''
            SELECT income_id, category, amount, date
            FROM incomes
        ''', conn)
    except Exception:
        inc_df = pd.DataFrame()

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pets")
    total_pets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pets WHERE status = 'Adopted'")
    adopted_pets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoption_requests")
    total_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoption_requests WHERE status = 'Approved' OR status = 'Completed'")
    approved_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes")
    total_income = cursor.fetchone()[0]

    # Category-wise adoption distribution
    category_summary = []
    if not pets_df.empty:
        cat_group = pets_df.groupby('category').agg(
            total=('pet_id', 'count'),
            adopted=('status', lambda s: (s == 'Adopted').sum()),
            available=('status', lambda s: (s == 'Available').sum())
        ).reset_index()
        category_summary = cat_group.to_dict(orient='records')

    # Income by category
    income_by_category = []
    if not inc_df.empty:
        inc_group = inc_df.groupby('category')['amount'].sum().reset_index()
        income_by_category = inc_group.to_dict(orient='records')

    # Status distribution
    status_summary = []
    if not req_df.empty:
        req_status = req_df.groupby('status')['request_id'].count().reset_index()
        req_status.rename(columns={'request_id': 'count'}, inplace=True)
        status_summary = req_status.to_dict(orient='records')

    conn.close()
    return render_template(
        'reports.html',
        total_pets=total_pets,
        adopted_pets=adopted_pets,
        total_requests=total_requests,
        approved_requests=approved_requests,
        total_income=total_income,
        category_summary=category_summary,
        income_by_category=income_by_category,
        status_summary=status_summary
    )

@app.route('/reports/chart.png')
def generate_chart_png():
    """Generates a high-resolution Matplotlib graphical summary as required by Section 2.3 & FR-06."""
    conn = database.get_db()
    pets_df = pd.read_sql_query('''
        SELECT c.name as category,
               SUM(CASE WHEN p.status = 'Adopted' THEN 1 ELSE 0 END) as adopted,
               SUM(CASE WHEN p.status = 'Available' THEN 1 ELSE 0 END) as available
        FROM pet_categories c
        LEFT JOIN pets p ON c.category_id = p.category_id
        GROUP BY c.name
    ''', conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#f8fafc')

    if not pets_df.empty:
        x = np.arange(len(pets_df['category']))
        width = 0.35
        rects1 = ax.bar(x - width/2, pets_df['available'], width, label='Available Pets', color='#38bdf8')
        rects2 = ax.bar(x + width/2, pets_df['adopted'], width, label='Adopted Pets', color='#34d399')

        ax.set_ylabel('Number of Animals', fontsize=11, fontweight='bold', color='#334155')
        ax.set_title('Category-Wise Pet Adoptions & Availability Overview', fontsize=13, fontweight='bold', pad=15, color='#0f172a')
        ax.set_xticks(x)
        ax.set_xticklabels(pets_df['category'], fontsize=10, fontweight='600', color='#475569')
        ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0')
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for rect in rects1 + rects2:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{int(height)}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
    else:
        ax.text(0.5, 0.5, 'No pet data available', horizontalalignment='center', verticalalignment='center')

    plt.tight_layout()
    output = io.BytesIO()
    fig.savefig(output, format='png')
    plt.close(fig)
    output.seek(0)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/export/<dataset>')
@login_required
def export_csv(dataset):
    """FR-07: Export adoption request data, pets, or income data to CSV."""
    conn = database.get_db()
    cursor = conn.cursor()
    si = io.StringIO()
    cw = csv.writer(si)

    filename = f"{dataset}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if dataset == 'requests':
        cursor.execute('''
            SELECT r.request_id, u.name as applicant_name, u.email, u.phone,
                   p.name as pet_name, p.breed, r.request_date, r.status,
                   r.applicant_income, r.household_type, r.message, r.decision_date, r.notes
            FROM adoption_requests r
            JOIN users u ON r.user_id = u.user_id
            JOIN pets p ON r.pet_id = p.pet_id
            ORDER BY r.request_id DESC
        ''')
        rows = cursor.fetchall()
        headers = ['Request ID', 'Applicant Name', 'Email', 'Phone', 'Pet Name', 'Breed', 'Request Date', 'Status', 'Applicant Income (INR)', 'Household Type', 'Motivation Message', 'Decision Date', 'Notes']
    elif dataset == 'pets':
        cursor.execute('''
            SELECT p.pet_id, p.name, c.name as category, p.breed, p.age, p.gender,
                   p.status, p.adoption_fee, p.created_at
            FROM pets p
            JOIN pet_categories c ON p.category_id = c.category_id
            ORDER BY p.pet_id DESC
        ''')
        rows = cursor.fetchall()
        headers = ['Pet ID', 'Pet Name', 'Category', 'Breed', 'Age', 'Gender', 'Status', 'Adoption Fee (INR)', 'Registered Date']
    elif dataset == 'income':
        cursor.execute('''
            SELECT i.income_id, i.date, i.category, i.amount, i.payment_method, i.description, u.name as recorder
            FROM incomes i
            LEFT JOIN users u ON i.user_id = u.user_id
            ORDER BY i.date DESC
        ''')
        rows = cursor.fetchall()
        headers = ['Income ID', 'Date', 'Category', 'Amount (INR)', 'Payment Method', 'Description', 'Recorded By']
    else:
        conn.close()
        flash('Invalid dataset for export.', 'danger')
        return redirect(url_for('reports'))

    conn.close()
    cw.writerow(headers)
    for r in rows:
        cw.writerow(list(r))

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

# ==========================================
# 5. ADMIN / STAFF PORTAL (Manage Pets, Medical, Categories, Users)
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role in ['admin', 'staff']:
        conn = database.get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM pets")
        total_pets = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM adoption_requests WHERE status = 'Pending'")
        pending_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'adopter'")
        total_adopters = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM incomes")
        total_income = cursor.fetchone()[0]

        # Recent adoption requests
        cursor.execute('''
            SELECT r.*, u.name as user_name, p.name as pet_name, p.breed
            FROM adoption_requests r
            JOIN users u ON r.user_id = u.user_id
            JOIN pets p ON r.pet_id = p.pet_id
            ORDER BY r.request_id DESC LIMIT 5
        ''')
        recent_requests = cursor.fetchall()

        # Pet list
        cursor.execute('''
            SELECT p.*, c.name as category_name
            FROM pets p
            JOIN pet_categories c ON p.category_id = c.category_id
            ORDER BY p.pet_id DESC
        ''')
        all_pets = cursor.fetchall()

        conn.close()
        return render_template(
            'admin_dashboard.html',
            total_pets=total_pets,
            pending_requests=pending_requests,
            total_adopters=total_adopters,
            total_income=total_income,
            recent_requests=recent_requests,
            pets=all_pets
        )
    else:
        # Adopter dashboard
        return redirect(url_for('my_requests'))

@app.route('/admin/pet/add', methods=['GET', 'POST'])
@staff_or_admin_required
def add_pet():
    conn = database.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        breed = request.form.get('breed', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        description = request.form.get('description', '').strip()
        fee_raw = request.form.get('adoption_fee', '0').strip()
        status = request.form.get('status', 'Available')

        # File upload handling
        image_path = '/static/images/dog1.jpg'
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_name = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], save_name))
                image_path = f"/static/uploads/{save_name}"
        elif request.form.get('image_url'):
            image_path = request.form.get('image_url').strip()

        try:
            adoption_fee = float(fee_raw)
            if adoption_fee < 0:
                flash('Adoption fee cannot be negative.', 'danger')
                cursor.execute("SELECT * FROM pet_categories")
                categories = cursor.fetchall()
                conn.close()
                return render_template('pet_form.html', categories=categories, action='Add')
        except ValueError:
            adoption_fee = 0.0

        cursor.execute('''
            INSERT INTO pets (category_id, name, breed, age, gender, description, status, image_path, adoption_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (category_id, name, breed, age, gender, description, status, image_path, adoption_fee))
        pet_id = cursor.lastrowid

        # Initial medical log if provided
        vaccination = request.form.get('vaccination', '').strip()
        health_status = request.form.get('health_status', 'Healthy')
        if vaccination:
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                INSERT INTO medical_records (pet_id, vaccination, health_status, record_date, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (pet_id, vaccination, health_status, today, 'Initial admission medical examination'))

        conn.commit()
        conn.close()
        flash(f'Pet "{name}" registered successfully!', 'success')
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM pet_categories")
    categories = cursor.fetchall()
    conn.close()
    return render_template('pet_form.html', categories=categories, action='Add', pet=None)

@app.route('/admin/pet/edit/<int:pet_id>', methods=['GET', 'POST'])
@staff_or_admin_required
def edit_pet(pet_id):
    conn = database.get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pets WHERE pet_id = ?", (pet_id,))
    pet = cursor.fetchone()
    if not pet:
        conn.close()
        flash('Pet record not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id', type=int)
        breed = request.form.get('breed', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', 'Male')
        description = request.form.get('description', '').strip()
        fee_raw = request.form.get('adoption_fee', '0').strip()
        status = request.form.get('status', 'Available')

        image_path = pet['image_path']
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                save_name = f"{int(datetime.now().timestamp())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], save_name))
                image_path = f"/static/uploads/{save_name}"
        elif request.form.get('image_url'):
            image_path = request.form.get('image_url').strip()

        try:
            adoption_fee = float(fee_raw)
            if adoption_fee < 0:
                flash('Adoption fee cannot be negative.', 'danger')
                cursor.execute("SELECT * FROM pet_categories")
                categories = cursor.fetchall()
                conn.close()
                return render_template('pet_form.html', categories=categories, action='Edit', pet=pet)
        except ValueError:
            adoption_fee = 0.0

        cursor.execute('''
            UPDATE pets
            SET category_id = ?, name = ?, breed = ?, age = ?, gender = ?,
                description = ?, status = ?, image_path = ?, adoption_fee = ?
            WHERE pet_id = ?
        ''', (category_id, name, breed, age, gender, description, status, image_path, adoption_fee, pet_id))

        conn.commit()
        conn.close()
        flash(f'Pet record "{name}" updated successfully.', 'success')
        return redirect(url_for('dashboard'))

    cursor.execute("SELECT * FROM pet_categories")
    categories = cursor.fetchall()
    conn.close()
    return render_template('pet_form.html', categories=categories, action='Edit', pet=pet)

@app.route('/admin/pet/delete/<int:pet_id>', methods=['POST'])
@staff_or_admin_required
def delete_pet(pet_id):
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pets WHERE pet_id = ?", (pet_id,))
    conn.commit()
    conn.close()
    flash('Pet listing deleted successfully.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/admin/medical/add/<int:pet_id>', methods=['POST'])
@staff_or_admin_required
def add_medical_record(pet_id):
    vaccination = request.form.get('vaccination', '').strip()
    health_status = request.form.get('health_status', 'Healthy')
    record_date = request.form.get('record_date', datetime.now().strftime('%Y-%m-%d'))
    notes = request.form.get('notes', '').strip()

    if not vaccination:
        flash('Vaccination details are required.', 'danger')
        return redirect(url_for('pet_detail', pet_id=pet_id))

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO medical_records (pet_id, vaccination, health_status, record_date, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (pet_id, vaccination, health_status, record_date, notes))
    conn.commit()
    conn.close()
    flash('Medical record appended successfully.', 'success')
    return redirect(url_for('pet_detail', pet_id=pet_id))

@app.route('/admin/categories', methods=['GET', 'POST'])
@staff_or_admin_required
def manage_categories():
    conn = database.get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        icon = request.form.get('icon', 'fa-paw').strip()
        if name:
            try:
                cursor.execute("INSERT INTO pet_categories (name, description, icon) VALUES (?, ?, ?)", (name, description, icon))
                conn.commit()
                flash(f'Category "{name}" created.', 'success')
            except Exception:
                flash(f'Category "{name}" already exists.', 'danger')
        return redirect(url_for('manage_categories'))

    cursor.execute('''
        SELECT c.*, COUNT(p.pet_id) as pet_count
        FROM pet_categories c
        LEFT JOIN pets p ON c.category_id = p.category_id
        GROUP BY c.category_id
    ''')
    categories = cursor.fetchall()
    conn.close()
    return render_template('categories.html', categories=categories)

@app.route('/admin/users')
@admin_required
def manage_users():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.*, COUNT(r.request_id) as request_count
        FROM users u
        LEFT JOIN adoption_requests r ON u.user_id = r.user_id
        GROUP BY u.user_id
        ORDER BY u.user_id ASC
    ''')
    users_list = cursor.fetchall()
    conn.close()
    return render_template('users.html', users=users_list)

# ==========================================
# 6. TESTING, DEFECT REPORT & STLC (Section 12, BUG-001)
# ==========================================

@app.route('/defect-report')
def defect_report():
    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM defect_logs ORDER BY defect_id ASC")
    defects = cursor.fetchall()
    conn.close()
    return render_template('defect_report.html', defects=defects)

@app.route('/defect-report/log', methods=['POST'])
@login_required
def log_defect():
    defect_id = request.form.get('defect_id', '').strip()
    title = request.form.get('title', '').strip()
    module = request.form.get('module', '').strip()
    severity = request.form.get('severity', 'Medium')
    priority = request.form.get('priority', 'Medium')
    steps = request.form.get('steps', '').strip()
    expected = request.form.get('expected', '').strip()
    actual = request.form.get('actual', '').strip()
    status = request.form.get('status', 'New')

    if not defect_id or not title:
        flash('Defect ID and Title are required.', 'danger')
        return redirect(url_for('defect_report'))

    conn = database.get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO defect_logs (defect_id, title, module, severity, priority, steps, expected, actual, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (defect_id, title, module, severity, priority, steps, expected, actual, status))
        conn.commit()
        flash(f'Defect {defect_id} logged successfully into STLC registry.', 'success')
    except Exception as e:
        flash(f'Error logging defect: {str(e)}', 'danger')
    conn.close()
    return redirect(url_for('defect_report'))

# ==========================================
# 7. AUTHENTICATION (FR-01, SEL-02, SEL-03, SEL-09)
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip() or request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        # SEL-02: Valid login -> Dashboard opens
        # SEL-03: Invalid login -> Error displayed
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user['role'] in ['admin', 'staff']:
                return redirect(url_for('dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email address or password. Please verify and try again.', 'danger')
            return render_template('login.html', error="Invalid email or password", email=email)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        role = request.form.get('role', 'adopter')

        if not name or not email or not password:
            flash('Name, email, and password are required fields.', 'danger')
            return render_template('register.html')

        conn = database.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash('An account with this email address already exists.', 'warning')
            return render_template('register.html')

        hashed_pw = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, phone, address, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, hashed_pw, phone, address, role))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        new_user = cursor.fetchone()
        conn.close()

        session['user_id'] = new_user['user_id']
        session['name'] = new_user['name']
        session['email'] = new_user['email']
        session['role'] = new_user['role']

        flash('Registration completed successfully! Welcome to Pet Adoption Portal.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    # SEL-09: Logout -> Session ends
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('login'))

@app.route('/reviews/add/<int:pet_id>', methods=['POST'])
@login_required
def add_review(pet_id):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or rating < 1 or rating > 5 or not comment:
        flash('Please provide both a valid rating (1-5) and feedback comment.', 'danger')
        return redirect(url_for('pet_detail', pet_id=pet_id))

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reviews (user_id, pet_id, rating, comment)
        VALUES (?, ?, ?, ?)
    ''', (session['user_id'], pet_id, rating, comment))
    conn.commit()
    conn.close()
    flash('Thank you for sharing your feedback and review!', 'success')
    return redirect(url_for('pet_detail', pet_id=pet_id))

# API Endpoint for quick asynchronous testing or health checks
@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'healthy',
        'service': 'Pet Adoption Portal',
        'timestamp': datetime.now().isoformat(),
        'college': 'Government Polytechnic Pune',
        'course': 'Software Engineering and Testing (CM41206)'
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
