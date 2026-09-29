import os
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from data_store import LocalDataStore

# AWS Region & SNS Topic configuration
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
USERS_TABLE_NAME = os.getenv("DYNAMODB_USERS_TABLE", "TravelGo_Users")
BOOKINGS_TABLE_NAME = os.getenv("DYNAMODB_BOOKINGS_TABLE", "TravelGo_Bookings")
SNS_TOPIC_ARN = os.getenv("TRAVELGO_SNS_TOPIC_ARN", "")

local_db = LocalDataStore()

class AWSManager:
    def __init__(self):
        self.dynamodb = None
        self.sns = None
        self.users_table = None
        self.bookings_table = None
        self.aws_available = False
        self.init_aws()

    def init_aws(self):
        """Attempts to initialize boto3 DynamoDB and SNS clients."""
        try:
            # Check if AWS credentials exist or if boto3 can create a session
            session = boto3.Session(region_name=AWS_REGION)
            credentials = session.get_credentials()
            
            if credentials and credentials.access_key:
                self.dynamodb = session.resource('dynamodb')
                self.sns = session.client('sns')
                self.users_table = self.dynamodb.Table(USERS_TABLE_NAME)
                self.bookings_table = self.dynamodb.Table(BOOKINGS_TABLE_NAME)
                
                # Check if table exists or verify connectivity
                self.users_table.table_status
                self.aws_available = True
                print(f"[AWS Manager] Successfully connected to AWS DynamoDB ({USERS_TABLE_NAME}, {BOOKINGS_TABLE_NAME}) and SNS!")
            else:
                print("[AWS Manager] AWS credentials not found. Falling back to local data store.")
                self.aws_available = False
        except Exception as e:
            print(f"[AWS Manager] AWS initialization notice: {e}. Operating in Local Fallback mode.")
            self.aws_available = False

    def create_tables_if_not_exist(self):
        """Helper to auto-create DynamoDB tables if Troven/AWS sandbox is active."""
        if not self.aws_available:
            return False, "AWS not available"
        
        try:
            existing_tables = self.dynamodb.meta.client.list_tables()['TableNames']
            
            # Users table (PK: email)
            if USERS_TABLE_NAME not in existing_tables:
                self.dynamodb.create_table(
                    TableName=USERS_TABLE_NAME,
                    KeySchema=[{'AttributeName': 'email', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'email', 'AttributeType': 'S'}],
                    BillingMode='PAY_PER_REQUEST'
                )
                print(f"Created DynamoDB Table: {USERS_TABLE_NAME}")

            # Bookings table (PK: booking_id)
            if BOOKINGS_TABLE_NAME not in existing_tables:
                self.dynamodb.create_table(
                    TableName=BOOKINGS_TABLE_NAME,
                    KeySchema=[{'AttributeName': 'booking_id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[
                        {'AttributeName': 'booking_id', 'AttributeType': 'S'}
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                print(f"Created DynamoDB Table: {BOOKINGS_TABLE_NAME}")
                
            return True, "DynamoDB tables created or already exist."
        except Exception as e:
            return False, str(e)

    # --- USER OPERATIONS ---
    def get_user_by_email(self, email):
        email_clean = email.lower().strip()
        if self.aws_available:
            try:
                res = self.users_table.get_item(Key={'email': email_clean})
                return res.get('Item')
            except Exception as e:
                print(f"DynamoDB get_user error: {e}. Falling back to local.")
        return local_db.get_user_by_email(email_clean)

    def create_user(self, email, name, password):
        email_clean = email.lower().strip()
        user_exists = self.get_user_by_email(email_clean)
        if user_exists:
            return False, "User already exists with this email address."
            
        success, user_data = local_db.create_user(email_clean, name, password)
        
        if success and self.aws_available:
            try:
                item = {
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'password': user_data['password'],
                    'created_at': user_data['created_at'],
                    'logins': user_data.get('logins', [])
                }
                self.users_table.put_item(Item=item)
                print(f"[DynamoDB] Saved user {email_clean} to DynamoDB.")
            except Exception as e:
                print(f"[DynamoDB] User put_item failed: {e}")
                
        return success, user_data

    def verify_user(self, email, password):
        user = self.get_user_by_email(email)
        if not user:
            return None
        from werkzeug.security import check_password_hash
        if check_password_hash(user['password'], password):
            return user
        return None

    # --- BOOKING OPERATIONS ---
    def create_booking(self, booking_data):
        # Always create in local data store for instant reliability
        new_booking = local_db.create_booking(booking_data)
        
        # Sync with AWS DynamoDB if available
        if self.aws_available:
            try:
                # Convert float price to string/Decimal for DynamoDB
                item = dict(new_booking)
                item['price'] = str(item['price'])
                self.bookings_table.put_item(Item=item)
                print(f"[DynamoDB] Saved booking {new_booking['booking_id']} to DynamoDB.")
            except Exception as e:
                print(f"[DynamoDB] Booking put_item failed: {e}")
                
        # Send AWS SNS Notification
        sns_result = self.send_sns_notification(new_booking, action="CONFIRMATION")
        new_booking['sns_notification'] = sns_result
        return new_booking

    def get_user_bookings(self, email):
        email_clean = email.lower().strip()
        if self.aws_available:
            try:
                # Scan table for user email
                response = self.bookings_table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('email').eq(email_clean)
                )
                items = response.get('Items', [])
                if items:
                    # Convert price back to float
                    for item in items:
                        item['price'] = float(item.get('price', 0))
                    # Sort by created_at desc
                    items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                    return items
            except Exception as e:
                print(f"[DynamoDB] get_user_bookings scan error: {e}. Using local store.")
                
        return local_db.get_bookings(email_clean)

    def cancel_booking(self, booking_id, email):
        success, booking = local_db.cancel_booking(booking_id, email)
        if success and booking:
            if self.aws_available:
                try:
                    self.bookings_table.update_item(
                        Key={'booking_id': booking_id},
                        UpdateExpression="set #s = :val",
                        ExpressionAttributeNames={'#s': 'status'},
                        ExpressionAttributeValues={':val': 'CANCELLED'}
                    )
                    print(f"[DynamoDB] Cancelled booking {booking_id} in DynamoDB.")
                except Exception as e:
                    print(f"[DynamoDB] Update item status failed: {e}")
            
            # Send AWS SNS Cancellation Notification
            sns_res = self.send_sns_notification(booking, action="CANCELLATION")
            booking['sns_notification'] = sns_res
            
        return success, booking

    # --- AWS SNS NOTIFICATION SERVICE ---
    def send_sns_notification(self, booking_data, action="CONFIRMATION"):
        """Publishes real-time travel confirmation or cancellation email via AWS SNS."""
        subject = f"TravelGo {action.title()}: Booking #{booking_data['booking_id']}"
        
        message_body = (
            f"=========================================\n"
            f"       TRAVELGO BOOKING {action.upper()}      \n"
            f"=========================================\n\n"
            f"Dear Customer ({booking_data['email']}),\n\n"
            f"Your booking status: {booking_data['status']}\n\n"
            f"Booking ID: {booking_data['booking_id']}\n"
            f"Travel Type: {booking_data['type'].upper()}\n"
            f"Details: {booking_data.get('details', 'N/A')}\n"
            f"Route/Destination: {booking_data.get('source', '')} -> {booking_data.get('destination', '')}\n"
            f"Date of Travel: {booking_data.get('date', 'N/A')}\n"
            f"Seat / Room Info: {booking_data.get('seat', 'N/A')}\n"
            f"Total Amount Paid: INR ₹{booking_data.get('price', 0):,.2f}\n"
            f"Payment Method: {booking_data.get('payment_method', 'N/A')}\n"
            f"Payment Reference: {booking_data.get('payment_reference', 'N/A')}\n\n"
            f"Thank you for choosing TravelGo!\n"
            f"Have a safe and enjoyable journey.\n\n"
            f"TravelGo Cloud Platform (Powered by AWS EC2 & DynamoDB)"
        )
        
        if self.aws_available and SNS_TOPIC_ARN:
            try:
                response = self.sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=message_body,
                    Subject=subject
                )
                print(f"[AWS SNS] Successfully published message ID: {response.get('MessageId')}")
                return {
                    "sent": True,
                    "provider": "AWS SNS",
                    "message_id": response.get('MessageId'),
                    "topic_arn": SNS_TOPIC_ARN,
                    "preview": message_body
                }
            except Exception as e:
                print(f"[AWS SNS] Publish error: {e}")
                return {
                    "sent": False,
                    "provider": "AWS SNS (Error)",
                    "error": str(e),
                    "preview": message_body
                }
        else:
            # Fallback simulator for SNS notification
            print(f"[SNS Simulation] Real-time email payload queued for {booking_data['email']}")
            return {
                "sent": True,
                "provider": "AWS SNS (Simulated / Local Log)",
                "message_id": f"SNS-MOCK-{booking_data['booking_id']}",
                "topic_arn": SNS_TOPIC_ARN or "arn:aws:sns:us-east-1:123456789012:TravelGoBookingsTopic",
                "preview": message_body
            }

aws_mgr = AWSManager()
