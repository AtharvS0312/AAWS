# TravelGo - Cloud-Based Travel Booking Platform

**TravelGo** is a full-stack, cloud-based travel booking platform designed to unify reservations for **Buses**, **Trains**, **Flights**, and **Hotels** under a single seamless interface. 

Built with **Flask** (Python) for backend processing, dynamic responsive HTML5/CSS3/JavaScript frontend templates, **Amazon EC2** for web hosting, **Amazon DynamoDB** for fast persistent storage, and **Amazon SNS (Simple Notification Service)** for real-time transactional email notifications.

---

## 🌟 Key Features

1. **Multi-Mode Travel Search & Reservation System**:
   - 🚌 **Buses**: Interactive 2D Seat Selection Grid (Lower & Upper sleeper decks, window preferences, real-time seat status).
   - 🚆 **Trains**: Search express train schedules, train numbers, availability statuses (1A, 2A, 3A, SL, EC, CC).
   - ✈️ **Flights**: Direct & layover flights with baggage allowances and cabin class selection.
   - 🏨 **Hotels**: Search and filter by category (Luxury, Mid-Range, Budget), star rating, price range slider, amenities, and room choices.

2. **Real-Time Notifications via AWS SNS**:
   - Automatic publication of transactional email alerts upon **Booking Confirmation** and **Booking Cancellation**.
   - Includes receipt details, payment reference numbers, seat/room assignments, and travel dates.

3. **Persistent Data Storage with DynamoDB & Local Fallback**:
   - `Users` Table (PK: `email`): Manages authentication, hashed passwords, and login history logs.
   - `Bookings` Table (PK: `booking_id`): Stores travel reservations, payment references, price breakdowns, and statuses (`CONFIRMED` / `CANCELLED`).
   - Seamless **Local Store Auto-Fallback** using persistent JSON structures when AWS credentials are not configured, enabling offline development and instant local testing.

4. **Dynamic User Dashboard**:
   - Personal travel history tracking for past and upcoming trips.
   - Filter by travel type (Bus, Train, Flight, Hotel) and status.
   - Quick AJAX cancellation workflow with instant UI status badge updates and SNS notification alerts.

5. **AWS Status & SNS Debugger**:
   - Interactive Admin view (`/admin`) to inspect AWS DynamoDB connectivity, table statuses, and trigger test SNS alerts.

---

## 🏗 System Architecture

```
                                +-------------------+
                                |     End User      |
                                |   (Web / Mobile)  |
                                +---------+---------+
                                          |
                                    HTTP/HTTPS
                                          |
                                          v
                              +-----------------------+
                              |   Flask Backend       |
                              |   (Amazon EC2)        |
                              +---+---------------+---+
                                  |               |
               Publish Payload    |               | Asynchronous DB Ops
               (boto3 SNS Client) |               | (boto3 Resource)
                                  v               v
                      +-------------------+   +--------------------+
                      |  Amazon SNS Topic |   |  Amazon DynamoDB   |
                      | (TravelGoBookings)|   | (Users & Bookings) |
                      +---------+---------+   +--------------------+
                                |
                        Email Confirmation
                                |
                                v
                      +-------------------+
                      |  User & Admin     |
                      |  Email Endpoints  |
                      +-------------------+
```

---

## 🚀 Quick Start Guide (Local Setup)

### 1. Prerequisites
- Python 3.9+
- pip

### 2. Installation
Clone or navigate to the project workspace and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and visit: `http://localhost:5000`

### 4. Quick Demo Login Credentials
For testing and evaluation:
- **Email**: `demo@travelgo.com`
- **Password**: `password123`

---

## ☁️ Troven Labs & AWS Cloud Integration Instructions

When Troven Labs access is activated:

### Step 1: Configure AWS Environment Variables
Set your temporary AWS credentials in your terminal or environment:
```bash
export AWS_ACCESS_KEY_ID="YOUR_TROVEN_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_TROVEN_SECRET_KEY"
export AWS_SESSION_TOKEN="YOUR_TROVEN_SESSION_TOKEN" # If applicable
export AWS_DEFAULT_REGION="us-east-1"
export TRAVELGO_SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:TravelGoBookingsTopic"
```

### Step 2: Auto-Provision DynamoDB Tables
Navigate to `http://localhost:5000/admin` in the app or run Python in terminal to create the tables automatically:
```python
from aws_config import aws_mgr
aws_mgr.create_tables_if_not_exist()
```

This provisions:
- `TravelGo_Users` (Partition Key: `email` [S])
- `TravelGo_Bookings` (Partition Key: `booking_id` [S])

### Step 3: Run on Amazon EC2
To deploy for high-availability production on EC2:
```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

## 🌐 Deployment on Render (render.com)

TravelGo is configured for deployment on **Render**:

### Option A: Automatic Blueprint Deployment
1. Push your repository to **GitHub**.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository. Render will automatically detect [`render.yaml`](file:///c:/Vedant78/AAWS/render.yaml) and configure the web service.

### Option B: Manual Web Service Setup
- **Environment**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variables** (Optional for AWS integration):
  - `SECRET_KEY`: Set a secure random string.
  - `AWS_DEFAULT_REGION`: `us-east-1`
  - `AWS_ACCESS_KEY_ID`: *(Optional)* Your AWS Access Key
  - `AWS_SECRET_ACCESS_KEY`: *(Optional)* Your AWS Secret Key
  - `TRAVELGO_SNS_TOPIC_ARN`: *(Optional)* Your AWS SNS Topic ARN

---

## 🧪 Running Automated Tests
Run the included test suite to verify all routes, booking flows, and SNS handlers:
```bash
python test_app.py
```

