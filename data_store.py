import json
import os
import uuid
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
BOOKINGS_FILE = os.path.join(DATA_DIR, 'bookings.json')

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        default_users = {
            "demo@travelgo.com": {
                "email": "demo@travelgo.com",
                "name": "Alex Morgan",
                "password": generate_password_hash("password123"),
                "logins": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)

    if not os.path.exists(BOOKINGS_FILE):
        default_bookings = [
            {
                "booking_id": "TG-BUS-98231",
                "email": "demo@travelgo.com",
                "type": "bus",
                "source": "Hyderabad",
                "destination": "Bangalore",
                "date": "2026-10-15",
                "seat": "L-08 (Window)",
                "details": "VRL Travels • Multi-Axle Volvo AC Sleeper",
                "price": 1250,
                "payment_method": "Credit Card",
                "payment_reference": "PAY-874920193",
                "status": "CONFIRMED",
                "created_at": "2026-09-20 14:30:00"
            },
            {
                "booking_id": "TG-HTL-44129",
                "email": "demo@travelgo.com",
                "type": "hotel",
                "source": "Chennai",
                "destination": "Chennai",
                "date": "2026-10-20",
                "seat": "Deluxe Sea View Room 304",
                "details": "The Grand Palace Resort • 4 Star Luxury",
                "price": 4500,
                "payment_method": "UPI / GPay",
                "payment_reference": "PAY-992104812",
                "status": "CONFIRMED",
                "created_at": "2026-09-22 09:15:00"
            }
        ]
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(default_bookings, f, indent=2)

class LocalDataStore:
    def __init__(self):
        ensure_data_dir()

    def get_users(self):
        ensure_data_dir()
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_users(self, users):
        ensure_data_dir()
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

    def get_user_by_email(self, email):
        users = self.get_users()
        return users.get(email.lower().strip())

    def create_user(self, email, name, password):
        users = self.get_users()
        email_clean = email.lower().strip()
        if email_clean in users:
            return False, "User already exists with this email address."
        
        users[email_clean] = {
            "email": email_clean,
            "name": name.strip(),
            "password": generate_password_hash(password),
            "logins": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_users(users)
        return True, users[email_clean]

    def verify_user(self, email, password):
        user = self.get_user_by_email(email)
        if not user:
            return None
        if check_password_hash(user['password'], password):
            # Record login timestamp
            users = self.get_users()
            email_clean = email.lower().strip()
            if email_clean in users:
                if 'logins' not in users[email_clean]:
                    users[email_clean]['logins'] = []
                users[email_clean]['logins'].append(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.save_users(users)
            return user
        return None

    def get_bookings(self, email=None):
        ensure_data_dir()
        try:
            with open(BOOKINGS_FILE, 'r') as f:
                bookings = json.load(f)
        except Exception:
            bookings = []
        
        if email:
            email_clean = email.lower().strip()
            return [b for b in bookings if b.get('email', '').lower() == email_clean]
        return bookings

    def create_booking(self, booking_data):
        ensure_data_dir()
        bookings = self.get_bookings()
        
        booking_id = f"TG-{booking_data.get('type', 'TRV').upper()[:3]}-{uuid.uuid4().hex[:6].upper()}"
        pay_ref = f"PAY-{uuid.uuid4().hex[:9].upper()}"
        
        new_booking = {
            "booking_id": booking_id,
            "email": booking_data['email'].lower().strip(),
            "type": booking_data['type'],
            "source": booking_data.get('source', ''),
            "destination": booking_data.get('destination', ''),
            "date": booking_data.get('date', ''),
            "seat": booking_data.get('seat', 'Standard'),
            "details": booking_data.get('details', ''),
            "price": float(booking_data.get('price', 0)),
            "payment_method": booking_data.get('payment_method', 'Credit Card'),
            "payment_reference": pay_ref,
            "status": "CONFIRMED",
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        bookings.insert(0, new_booking)
        with open(BOOKINGS_FILE, 'w') as f:
            json.dump(bookings, f, indent=2)
            
        return new_booking

    def cancel_booking(self, booking_id, email):
        ensure_data_dir()
        bookings = self.get_bookings()
        email_clean = email.lower().strip()
        updated = False
        target_booking = None
        
        for b in bookings:
            if b['booking_id'] == booking_id and b['email'].lower() == email_clean:
                b['status'] = "CANCELLED"
                updated = True
                target_booking = b
                break
                
        if updated:
            with open(BOOKINGS_FILE, 'w') as f:
                json.dump(bookings, f, indent=2)
            return True, target_booking
        return False, None


# Pre-configured catalog datasets for Bus, Train, Flight, Hotel search listings
SAMPLE_LISTINGS = {
    "buses": [
        {
            "id": "BUS-101",
            "operator": "VRL Travels",
            "bus_type": "Multi-Axle B11R Volvo AC Semi-Sleeper (2+2)",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "21:30",
            "arrival_time": "06:15",
            "duration": "8h 45m",
            "rating": 4.8,
            "reviews_count": 342,
            "price": 1250,
            "amenities": ["WiFi", "Charging Point", "Blanket", "Water Bottle", "Emergency Button"],
            "available_seats_count": 18
        },
        {
            "id": "BUS-102",
            "operator": "Orange Tours & Travels",
            "bus_type": "Scania AC Multi-Axle Sleeper (2+1)",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "22:00",
            "arrival_time": "06:45",
            "duration": "8h 45m",
            "rating": 4.6,
            "reviews_count": 218,
            "price": 1450,
            "amenities": ["Personal TV", "WiFi", "Reading Lamp", "Pillow", "Charging Point"],
            "available_seats_count": 12
        },
        {
            "id": "BUS-103",
            "operator": "KSRTC Swift",
            "bus_type": "Airavat Club Class AC Volvo",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "20:00",
            "arrival_time": "05:00",
            "duration": "9h 00m",
            "rating": 4.5,
            "reviews_count": 510,
            "price": 1100,
            "amenities": ["Water Bottle", "Blanket", "Reclining Seats"],
            "available_seats_count": 24
        },
        {
            "id": "BUS-104",
            "operator": "IntrCity SmartBus",
            "bus_type": "AC Sleeper 2+1 with Washroom",
            "source": "Chennai",
            "destination": "Bangalore",
            "departure_time": "23:15",
            "arrival_time": "05:30",
            "duration": "6h 15m",
            "rating": 4.7,
            "reviews_count": 189,
            "price": 990,
            "amenities": ["Washroom", "In-bus CCTV", "Live Tracking", "WiFi"],
            "available_seats_count": 15
        }
    ],
    "trains": [
        {
            "id": "TRN-12658",
            "train_number": "12658",
            "name": "Kacheguda - SBC Express",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "19:05",
            "arrival_time": "06:20",
            "duration": "11h 15m",
            "classes": [
                {"code": "1A", "name": "First AC", "price": 2850, "status": "AVAILABLE-06"},
                {"code": "2A", "name": "2 Tier AC", "price": 1680, "status": "AVAILABLE-14"},
                {"code": "3A", "name": "3 Tier AC", "price": 1180, "status": "AVAILABLE-32"},
                {"code": "SL", "name": "Sleeper", "price": 435, "status": "RAC-08"}
            ],
            "runs_on": "Daily"
        },
        {
            "id": "TRN-20607",
            "train_number": "20607",
            "name": "Vande Bharat Express",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "05:30",
            "arrival_time": "14:00",
            "duration": "8h 30m",
            "classes": [
                {"code": "EC", "name": "Executive Class", "price": 3100, "status": "AVAILABLE-12"},
                {"code": "CC", "name": "AC Chair Car", "price": 1620, "status": "AVAILABLE-45"}
            ],
            "runs_on": "Except Wed"
        },
        {
            "id": "TRN-12626",
            "train_number": "12626",
            "name": "Kerala Express",
            "source": "Chennai",
            "destination": "Bangalore",
            "departure_time": "21:40",
            "arrival_time": "04:15",
            "duration": "6h 35m",
            "classes": [
                {"code": "2A", "name": "2 Tier AC", "price": 1250, "status": "AVAILABLE-22"},
                {"code": "3A", "name": "3 Tier AC", "price": 890, "status": "AVAILABLE-64"},
                {"code": "SL", "name": "Sleeper", "price": 320, "status": "AVAILABLE-110"}
            ],
            "runs_on": "Daily"
        }
    ],
    "flights": [
        {
            "id": "FLT-6E504",
            "airline": "IndiGo",
            "flight_number": "6E-504",
            "logo": "indigo",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "07:15",
            "arrival_time": "08:25",
            "duration": "1h 10m",
            "stops": "Non-stop",
            "price": 3499,
            "class": "Economy",
            "baggage": "15 kg Check-in, 7 kg Cabin"
        },
        {
            "id": "FLT-UK882",
            "airline": "Vistara",
            "flight_number": "UK-882",
            "logo": "vistara",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "18:40",
            "arrival_time": "19:55",
            "duration": "1h 15m",
            "stops": "Non-stop",
            "price": 4290,
            "class": "Premium Economy",
            "baggage": "20 kg Check-in, 7 kg Cabin"
        },
        {
            "id": "FLT-AI512",
            "airline": "Air India",
            "flight_number": "AI-512",
            "logo": "airindia",
            "source": "Hyderabad",
            "destination": "Bangalore",
            "departure_time": "11:30",
            "arrival_time": "12:40",
            "duration": "1h 10m",
            "stops": "Non-stop",
            "price": 3850,
            "class": "Economy",
            "baggage": "25 kg Check-in, 8 kg Cabin"
        }
    ],
    "hotels": [
        {
            "id": "HTL-001",
            "name": "The Grand Palace Resort & Spa",
            "city": "Chennai",
            "address": "ECR Beach Road, Chennai",
            "category": "Luxury",
            "star_rating": 5,
            "price_per_night": 4500,
            "rating": 4.9,
            "reviews": 482,
            "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80",
            "amenities": ["Swimming Pool", "Spa & Wellness", "Free WiFi", "Buffet Breakfast", "Ocean View", "Fitness Center"],
            "rooms": [
                {"name": "Deluxe Sea View Room", "price": 4500, "capacity": "2 Adults"},
                {"name": "Executive Ocean Suite", "price": 7200, "capacity": "3 Adults"}
            ]
        },
        {
            "id": "HTL-002",
            "name": "Taj Residency & Business Hub",
            "city": "Bangalore",
            "address": "MG Road, Indiranagar, Bangalore",
            "category": "Luxury",
            "star_rating": 5,
            "price_per_night": 5800,
            "rating": 4.8,
            "reviews": 620,
            "image": "https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800&q=80",
            "amenities": ["Rooftop Bar", "High-speed WiFi", "Valet Parking", "Airport Shuttle", "Breakfast Included"],
            "rooms": [
                {"name": "City View King Room", "price": 5800, "capacity": "2 Adults"},
                {"name": "Club Presidential Suite", "price": 9500, "capacity": "2 Adults"}
            ]
        },
        {
            "id": "HTL-003",
            "name": "Hyatt Centric Gachibowli",
            "city": "Hyderabad",
            "address": "Financial District, Gachibowli, Hyderabad",
            "category": "Mid-Range",
            "star_rating": 4,
            "price_per_night": 3200,
            "rating": 4.6,
            "reviews": 310,
            "image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80",
            "amenities": ["Swimming Pool", "Gym", "Restaurant", "24/7 Room Service", "Free Parking"],
            "rooms": [
                {"name": "Standard King Room", "price": 3200, "capacity": "2 Adults"},
                {"name": "Deluxe Twin Bed Room", "price": 3800, "capacity": "2 Adults"}
            ]
        },
        {
            "id": "HTL-004",
            "name": "Backpackers Express Stay",
            "city": "Bangalore",
            "address": "Koramangala 4th Block, Bangalore",
            "category": "Budget",
            "star_rating": 3,
            "price_per_night": 1200,
            "rating": 4.3,
            "reviews": 195,
            "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
            "amenities": ["Free WiFi", "Co-working Space", "Cafeteria", "AC Rooms"],
            "rooms": [
                {"name": "Private Single AC Pod", "price": 1200, "capacity": "1 Adult"},
                {"name": "Private Double Room", "price": 1800, "capacity": "2 Adults"}
            ]
        }
    ]
}
