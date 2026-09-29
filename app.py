import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from aws_config import aws_mgr, local_db
from data_store import SAMPLE_LISTINGS

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "travelgo_secret_cloud_key_2026_x891")

# Helper function to inject current user into all template contexts
@app.context_processor
def inject_user_context():
    user = None
    if 'user_email' in session:
        user = aws_mgr.get_user_by_email(session['user_email'])
    return dict(
        current_user=user,
        aws_available=aws_mgr.aws_available,
        current_year=datetime.datetime.now().year
    )

# --- ROUTES ---

@app.route('/')
def index():
    """Home Page with unified search tabs (Bus, Train, Flight, Hotel)."""
    return render_template('index.html', listings=SAMPLE_LISTINGS)

@app.route('/search')
def search():
    """Search and filter listings for Transportation and Hotels."""
    travel_type = request.args.get('type', 'bus').lower()
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    category = request.args.get('category', 'all')
    max_price = request.args.get('max_price', type=float)
    
    results = SAMPLE_LISTINGS.get(travel_type + 'es' if travel_type == 'bus' else travel_type + 's', [])
    
    # Filtering logic
    filtered = []
    for item in results:
        match = True
        if source and 'source' in item:
            if source.lower() not in item['source'].lower():
                match = False
        if destination and 'destination' in item:
            if destination.lower() not in item['destination'].lower():
                match = False
        if destination and travel_type == 'hotel' and 'city' in item:
            if destination.lower() not in item['city'].lower():
                match = False
        if category != 'all':
            if travel_type == 'hotel' and item.get('category', '').lower() != category.lower():
                match = False
        if max_price:
            price = item.get('price') or item.get('price_per_night') or 0
            if price > max_price:
                match = False
        if match:
            filtered.append(item)
            
    return render_template('search.html', 
                           travel_type=travel_type,
                           source=source,
                           destination=destination,
                           date=date,
                           category=category,
                           max_price=max_price,
                           results=filtered)

@app.route('/bus/<bus_id>/seats')
def bus_seats(bus_id):
    """Interactive Bus Seat Selection Interface."""
    bus = next((b for b in SAMPLE_LISTINGS['buses'] if b['id'] == bus_id), None)
    if not bus:
        flash("Bus listing not found.", "danger")
        return redirect(url_for('search', type='bus'))
        
    date = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    return render_template('bus_seats.html', bus=bus, date=date)

@app.route('/hotel/<hotel_id>')
def hotel_details(hotel_id):
    """Hotel Detail & Room Selection View."""
    hotel = next((h for h in SAMPLE_LISTINGS['hotels'] if h['id'] == hotel_id), None)
    if not hotel:
        flash("Hotel listing not found.", "danger")
        return redirect(url_for('search', type='hotel'))
        
    date = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    return render_template('hotel_details.html', hotel=hotel, date=date)

@app.route('/booking/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout Summary page before confirmation."""
    if 'user_email' not in session:
        flash("Please log in to complete your booking.", "info")
        session['next_url'] = request.url
        return redirect(url_for('login'))

    if request.method == 'POST':
        item_id = request.form.get('item_id')
        travel_type = request.form.get('type')
        date = request.form.get('date')
        seat = request.form.get('seat', 'Standard Seat')
        source = request.form.get('source', '')
        destination = request.form.get('destination', '')
        price = float(request.form.get('price', 0))
        details = request.form.get('details', '')
        
        # Taxes & Fees (5% GST)
        tax = round(price * 0.05, 2)
        total_price = round(price + tax, 2)
        
        booking_data = {
            'item_id': item_id,
            'type': travel_type,
            'date': date,
            'seat': seat,
            'source': source,
            'destination': destination,
            'price': total_price,
            'base_price': price,
            'tax': tax,
            'details': details
        }
        return render_template('booking_confirm.html', booking=booking_data)
        
    return redirect(url_for('index'))

@app.route('/booking/process', methods=['POST'])
def process_booking():
    """Finalizing booking, storing in DynamoDB/Local DB and triggering AWS SNS email notification."""
    if 'user_email' not in session:
        flash("Please log in to proceed.", "danger")
        return redirect(url_for('login'))

    user_email = session['user_email']
    travel_type = request.form.get('type')
    source = request.form.get('source', '')
    destination = request.form.get('destination', '')
    date = request.form.get('date', '')
    seat = request.form.get('seat', 'Standard Seat')
    details = request.form.get('details', '')
    price = request.form.get('price', 0)
    payment_method = request.form.get('payment_method', 'Credit Card')

    booking_payload = {
        'email': user_email,
        'type': travel_type,
        'source': source,
        'destination': destination,
        'date': date,
        'seat': seat,
        'details': details,
        'price': price,
        'payment_method': payment_method
    }

    # Store in database and send SNS notification
    new_booking = aws_mgr.create_booking(booking_payload)

    flash(f"Booking Confirmed! Booking ID: {new_booking['booking_id']}. Confirmation email triggered via AWS SNS.", "success")
    return render_template('booking_success.html', booking=new_booking)

@app.route('/dashboard')
def dashboard():
    """User Personal Travel History Dashboard with past and upcoming bookings."""
    if 'user_email' not in session:
        flash("Please log in to view your dashboard.", "warning")
        return redirect(url_for('login'))

    user_email = session['user_email']
    bookings = aws_mgr.get_user_bookings(user_email)

    # Compute stats
    confirmed_count = sum(1 for b in bookings if b.get('status') == 'CONFIRMED')
    cancelled_count = sum(1 for b in bookings if b.get('status') == 'CANCELLED')
    total_spent = sum(b.get('price', 0) for b in bookings if b.get('status') == 'CONFIRMED')

    return render_template('dashboard.html', 
                           bookings=bookings, 
                           confirmed_count=confirmed_count,
                           cancelled_count=cancelled_count,
                           total_spent=total_spent)

@app.route('/booking/<booking_id>/cancel', methods=['POST'])
def cancel_booking_route(booking_id):
    """Cancel a booking and trigger real-time AWS SNS notification."""
    if 'user_email' not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_email = session['user_email']
    success, booking = aws_mgr.cancel_booking(booking_id, user_email)

    if success:
        return jsonify({
            "success": True, 
            "message": f"Booking {booking_id} cancelled successfully. AWS SNS alert sent.",
            "booking": booking
        })
    else:
        return jsonify({"success": False, "message": "Booking not found or could not be cancelled."}), 400

# --- AUTHENTICATION ---

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = aws_mgr.verify_user(email, password)
        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            flash(f"Welcome back, {user['name']}!", "success")
            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for('dashboard'))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        success, user_or_err = aws_mgr.create_user(email, name, password)
        if success:
            session['user_email'] = user_or_err['email']
            session['user_name'] = user_or_err['name']
            flash("Account created successfully! Welcome to TravelGo.", "success")
            return redirect(url_for('dashboard'))
        else:
            flash(user_or_err, "danger")

    return render_template('register.html')

@app.route('/auth/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('index'))

# --- ADMIN / AWS HEALTH CHECK ---

@app.route('/admin')
def admin():
    """AWS Cloud Status and Data Inspector Dashboard."""
    tables_status, msg = aws_mgr.create_tables_if_not_exist() if aws_mgr.aws_available else (False, "Local Store Mode")
    return render_template('admin.html', 
                           aws_available=aws_mgr.aws_available,
                           region=aws_mgr.aws_mgr if hasattr(aws_mgr, 'region') else os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
                           tables_status=tables_status,
                           msg=msg,
                           all_bookings=local_db.get_bookings())

@app.route('/api/sns-test', methods=['POST'])
def test_sns():
    """Trigger a test SNS Email Notification."""
    email = session.get('user_email', 'demo@travelgo.com')
    sample_booking = {
        'booking_id': 'TG-TEST-999',
        'email': email,
        'type': 'test',
        'source': 'Hyderabad',
        'destination': 'Cloud Lab',
        'date': datetime.date.today().strftime('%Y-%m-%d'),
        'seat': 'A1-AWS',
        'details': 'AWS SNS Integration Test Notification',
        'price': 100.0,
        'payment_method': 'Test Gateway',
        'payment_reference': 'TEST-PAY-12345',
        'status': 'CONFIRMED'
    }
    res = aws_mgr.send_sns_notification(sample_booking, action="TEST ALERT")
    return jsonify(res)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() in ["true", "1"])

