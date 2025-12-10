from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db import connection, OperationalError, transaction
from .models import Customer, Service
from .auth_helpers import (
    get_customer_from_session, customer_login, customer_logout, customer_required,
    get_admin_from_session, admin_login, admin_logout, admin_required
)
from datetime import datetime, date, time, timedelta
from collections import OrderedDict
from decimal import Decimal
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

CATEGORY_ORDER = ['Deals', 'Hair', 'Waxing', 'Threading', 'Facial', 'Nails']


def _format_price(value):
    if value is None:
        return '$0.00'
    return f"${Decimal(value):,.2f}"


def _get_service_image(service_name):
    """Map service name to image filename"""
    import os
    from django.conf import settings
    
    # Normalize service name for matching (lowercase, remove special chars)
    normalized_name = service_name.lower().strip()
    
    # Comprehensive mapping of service name keywords to image filenames
    # Order matters - more specific matches should come first
    image_mapping = [
        # Threading services
        ('eyebrow threading', 'eyebrow threading.jpeg'),
        ('facial threading', 'face threading.jpeg'),
        ('threading face', 'threading face.jpg'),
        ('threading', 'Threading.jpeg'),
        
        # Facial services
        ('deep cleansing facial', 'Deep Cleaning Facial.jpeg'),
        ('deep cleaning facial', 'Deep Cleaning Facial.jpeg'),
        ('facial treatment', 'Facial Treatment.jpg'),
        ('hydra facial', 'Hydra Facial.jpeg'),
        ('facial', 'Facial.jpeg'),
        
        # Hair services
        ('hair color', 'hair color.jpg'),
        ('hair colour', 'hair color.jpg'),
        ('hair coloring', 'hair color.jpg'),
        ('hair cut', 'hair cut img.webp'),
        ('haircut', 'hair cut img.webp'),
        ('hair wash', 'Hair wash.jpg'),
        ('styling', 'hair cut img.webp'),
        
        # Nail services
        ('nail art', 'Nails Art.jpeg'),
        ('nails art', 'Nails Art.jpeg'),
        ('manicure & pedicure', 'Pedicure & manicure.jpeg'),
        ('pedicure & manicure', 'Pedicure & manicure.jpeg'),
        ('manicure', 'Manicure.jpeg'),
        ('pedicure', 'Pedicure.jpeg'),
        ('nails', 'Nails.jpeg'),
        
        # Waxing services
        ('full body wax', 'waxing.jpg'),
        ('full body waxing', 'waxing.jpg'),
        ('waxing', 'waxing.jpg'),
    ]
    
    # Try to find matching image (check in order for most specific match first)
    for key, image_file in image_mapping:
        if key in normalized_name:
            image_path = os.path.join(settings.BASE_DIR, 'Assets', 'service images', image_file)
            if os.path.exists(image_path):
                # Return URL path for serving images
                from urllib.parse import quote
                encoded_filename = quote(image_file)
                return f'/service-images/{encoded_filename}'
    
    return None


def _service_to_dict(service):
    data = {
        'id': service.Service_ID,
        'name': service.ServiceName,
        'category': service.Category,
        'description': service.Description or '',
        'price': _format_price(service.Price),
        'original_price': _format_price(service.Original_Price) if getattr(service, 'Original_Price', None) else None,
        'discount': getattr(service, 'Discount_Label', None),
        'image': _get_service_image(service.ServiceName),
    }
    return data


def _get_services_data():
    services = list(Service.objects.filter(is_active=True).order_by('Category', 'ServiceName'))
    return [_service_to_dict(service) for service in services]


def _format_time_slot(value):
    if isinstance(value, time):
        return value.strftime('%I:%M %p')
    if hasattr(value, 'strftime'):
        return value.strftime('%I:%M %p')
    return value or ''


def _fetch_appointments_for_customer(customer_id):
    sql = """
        SELECT a.Appointment_ID,
               COALESCE(s.ServiceName, 'Scheduled Service') AS service_name,
               COALESCE(s.ServiceName, 'Scheduled Service appointment') AS service_description,
               COALESCE(p.Amount, 0) AS amount,
               a.Date,
               a.Time,
               COALESCE(a.Status, 'scheduled') AS status,
               CASE WHEN p.Status = 'completed' THEN 1 ELSE 0 END AS paid,
               e.Employee_ID,
               e.First_Name AS employee_first_name,
               e.Last_Name AS employee_last_name,
               e.Phone AS employee_phone,
               e.Rating AS employee_rating
        FROM APPOINTMENT a
        LEFT JOIN SALES s ON a.Sales_ID = s.Sales_ID
        LEFT JOIN PAYMENT p ON a.Payment_ID = p.Payment_ID
        LEFT JOIN EMPLOYEE e ON a.Employee_ID = e.Employee_ID
        WHERE a.Customer_ID = %s
        ORDER BY a.Date DESC, a.Time DESC
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [customer_id])
            rows = cursor.fetchall()
    except OperationalError:
        return []

    bookings = []
    for row in rows:
        service_name = row[1]
        employee_id = row[8]
        employee_first_name = row[9]
        employee_last_name = row[10]
        employee_phone = row[11]
        employee_rating = row[12]
        
        employee_name = None
        if employee_first_name and employee_last_name:
            employee_name = f"{employee_first_name} {employee_last_name}"
        elif employee_first_name:
            employee_name = employee_first_name
        
        bookings.append({
            'id': row[0],
            'service_name': service_name,
            'service_description': row[2],
            'service_price': _format_price(row[3]),
            'booking_date': row[4],
            'booking_time': _format_time_slot(row[5]),
            'status': row[6],
            'payment_completed': bool(row[7]),
            'service_image': _get_service_image(service_name),
            'employee_id': employee_id,
            'employee_name': employee_name,
            'employee_phone': employee_phone or 'N/A',
            'employee_rating': float(employee_rating) if employee_rating else None,
        })
    return bookings


def _fetch_receipts_for_customer(customer_id):
    sql = """
        SELECT r.Receipt_ID,
               COALESCE(s.ServiceName, 'Appointment Service') AS service_name,
               r.Amount,
               a.Date,
               a.Time,
               COALESCE(a.Status, 'completed') AS status,
               r.created_at
        FROM RECEIPTS r
        LEFT JOIN APPOINTMENT a ON r.Appointment_ID = a.Appointment_ID
        LEFT JOIN SALES s ON r.Sales_ID = s.Sales_ID
        WHERE r.Customer_ID = %s
        ORDER BY a.Date DESC, r.Receipt_ID DESC
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, [customer_id])
            rows = cursor.fetchall()
    except OperationalError:
        return []

    receipts = []
    for row in rows:
        service_name = row[1]
        receipts.append({
            'id': row[0],
            'service_name': service_name,
            'service_price': _format_price(row[2]),
            'booking_date': row[3],
            'booking_time': _format_time_slot(row[4]),
            'status': row[5],
            'created_at': row[6] or row[3],
            'service_image': _get_service_image(service_name),
        })
    return receipts


def _fetch_addresses_for_customer(customer):
    """Fetch addresses for customer - plain text format only"""
    if not customer.Address:
        return []
    
    addresses = []
    addresses.append({
        'id': 0,
        'full_address': customer.Address,
        'address_line1': '',
            'address_line2': '',
            'city': '',
            'state': '',
            'zip_code': '',
            'country': '',
            'is_default': True,
    })
    
    return addresses


def _normalize_time_slot(slot):
    if not slot:
        return None
    try:
        return datetime.strptime(slot.strip(), '%I:%M %p').strftime('%H:%M:%S')
    except ValueError:
        return slot


def _get_profile_display_name(customer):
    """Get display name from customer"""
    if customer:
        name = f"{customer.First_Name} {customer.Last_Name}".strip()
        return name if name else ''
    return ''


@csrf_protect
def login_view(request):
    # If already logged in, redirect appropriately
    customer = get_customer_from_session(request)
    admin = get_admin_from_session(request)
    
    if customer:
        return redirect(reverse('home'))
    elif admin:
        return redirect(reverse('admin_home'))
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'customer')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        
        if not mobile or not password:
            messages.error(request, 'Please enter login credentials.')
            return render(request, 'authentication/login.html')
        
        mobile = ''.join(filter(str.isdigit, mobile))
        
        try:
            db_executor = connection.cursor()
            
            db_executor.execute("SELECT Customer_ID, First_Name, Last_Name, Mobile_No, Password, Address FROM CUSTOMER WHERE Mobile_No = %s", [mobile])
            customer_row = db_executor.fetchone()
            
            if customer_row:
                stored_password = customer_row[4]
                if stored_password == password:
                    customer = Customer()
                    customer.Customer_ID = customer_row[0]
                    customer.First_Name = customer_row[1]
                    customer.Last_Name = customer_row[2]
                    customer.Mobile_No = customer_row[3]
                    customer.Password = customer_row[4]
                    customer.Address = customer_row[5] if len(customer_row) > 5 else None
                    
                    customer_login(request, customer)
                    messages.success(request, 'Login successful!')
                    return redirect('home')
            
            db_executor.execute("SELECT Admin_ID, First_Name, Last_Name, Mobile_No, Role, Password FROM ADMIN WHERE Mobile_No = %s", [mobile])
            admin_row = db_executor.fetchone()
            
            if admin_row:
                stored_password = admin_row[5]
                if stored_password == password:
                    admin = type('Admin', (), {})()
                    admin.Admin_ID = admin_row[0]
                    admin.First_Name = admin_row[1]
                    admin.Last_Name = admin_row[2]
                    admin.Mobile_No = admin_row[3]
                    admin.Role = admin_row[4]
                    admin.Password = admin_row[5]
                    
                    admin_login(request, admin)
                    messages.success(request, 'Admin login successful!')
                    return redirect(reverse('admin_home'))
            
            messages.error(request, 'Invalid mobile number or password.')
        except Exception:
            messages.error(request, 'An error occurred. Please try again.')
    
    return render(request, 'authentication/login.html')


@csrf_protect
def forgot_password_view(request):
    if get_customer_from_session(request):
        return redirect('home')
    if get_admin_from_session(request):
        return redirect('admin_home')
    
    user_data = None
    mobile_number = None
    user_type = None
    
    if request.method == 'POST':
        if 'search_mobile' in request.POST:
            mobile = request.POST.get('mobile', '').strip()
            mobile = ''.join(filter(str.isdigit, mobile))
            
            if not mobile:
                messages.error(request, 'Please enter a mobile number.')
                return render(request, 'authentication/forgot_password.html', {'user_data': None, 'mobile_number': None, 'user_type': None})
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT Customer_ID, First_Name, Last_Name, Mobile_No 
                        FROM CUSTOMER 
                        WHERE Mobile_No = %s
                    """, [mobile])
                    row = cursor.fetchone()
                    
                    if row:
                        user_data = {
                            'user_id': row[0],
                            'first_name': row[1],
                            'last_name': row[2],
                            'mobile_no': row[3]
                        }
                        user_type = 'customer'
                        mobile_number = mobile
                    else:
                        cursor.execute("""
                            SELECT Admin_ID, First_Name, Last_Name, Mobile_No, Role
                            FROM ADMIN 
                            WHERE Mobile_No = %s
                        """, [mobile])
                        row = cursor.fetchone()
                        
                        if row:
                            user_data = {
                                'user_id': row[0],
                                'first_name': row[1],
                                'last_name': row[2],
                                'mobile_no': row[3],
                                'role': row[4] if len(row) > 4 else None
                            }
                            user_type = 'admin'
                            mobile_number = mobile
                        else:
                            messages.error(request, 'Mobile number not found. Please check and try again.')
            except Exception:
                messages.error(request, 'An error occurred. Please try again.')
        
        elif 'save_password' in request.POST:
            user_id = request.POST.get('user_id')
            user_type = request.POST.get('user_type')
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            if not new_password or not confirm_password:
                messages.error(request, 'Please fill all password fields.')
                return render(request, 'authentication/forgot_password.html', {'user_data': None, 'mobile_number': None, 'user_type': None})
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'authentication/forgot_password.html', {'user_data': None, 'mobile_number': None, 'user_type': None})
            
            try:
                with connection.cursor() as cursor:
                    if user_type == 'customer':
                        cursor.execute("""
                            UPDATE CUSTOMER 
                            SET Password = %s, updated_at = NOW()
                            WHERE Customer_ID = %s
                        """, [new_password, user_id])
                    elif user_type == 'admin':
                        cursor.execute("""
                            UPDATE ADMIN 
                            SET Password = %s
                            WHERE Admin_ID = %s
                        """, [new_password, user_id])
                    
                    return render(request, 'authentication/forgot_password.html', {
                        'user_data': None,
                        'mobile_number': None,
                        'user_type': None,
                        'password_updated': True
                    })
            except Exception:
                messages.error(request, 'An error occurred while updating password. Please try again.')
    
    return render(request, 'authentication/forgot_password.html', {
        'user_data': user_data,
        'mobile_number': mobile_number,
        'user_type': user_type
    })


@csrf_protect
def signup_view(request):
    if get_customer_from_session(request):
        return redirect('home')
    
    if request.method == 'POST':
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Remove formatting characters from mobile number (keep only digits)
        mobile = ''.join(filter(str.isdigit, mobile))
        
        # Validation
        if not first_name or not last_name or not mobile or not password:
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'authentication/signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'authentication/signup.html')
        
        try:
            db_executor = connection.cursor()
            db_executor.execute("SELECT Customer_ID FROM CUSTOMER WHERE Mobile_No = %s", [mobile])
            if db_executor.fetchone():
                messages.error(request, 'User already exists with this mobile number. Please login.')
                return render(request, 'authentication/signup.html')
        except Exception:
            pass
        
        address = request.POST.get('address', '')
        
        try:
            with transaction.atomic():
                db_executor = connection.cursor()
                db_executor.execute("""
                    INSERT INTO CUSTOMER (First_Name, Last_Name, Mobile_No, Password, Address, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """, [first_name, last_name, mobile, password, address if address else None])
            
            
            messages.success(request, 'User added successfully!')
            return redirect('signup_success')
        except Exception as e:
            error_msg = str(e)
            if 'Duplicate entry' in error_msg or 'UNIQUE constraint' in error_msg:
                messages.error(request, 'User already exists with this mobile number. Please login.')
            else:
                messages.error(request, f'Failed to create account: {error_msg}. Please try again or contact support.')
            return render(request, 'authentication/signup.html')
    
    return render(request, 'authentication/signup.html')


def signup_success_view(request):
    """Success page after signup with auto-redirect to login after 5 seconds"""
    return render(request, 'authentication/signup_success.html')


def home_view(request):
    # Check if admin is logged in, redirect to admin home
    admin = get_admin_from_session(request)
    if admin:
        return redirect('admin_home')
    
    # Require customer login for customer home
    customer = get_customer_from_session(request)
    if not customer:
        messages.error(request, 'Please login to access this page.')
        return redirect('login')
    request.customer = customer
    services_data = _get_services_data()
    popular_services = services_data[:8]
    search_json = json.dumps(
        [{'name': service['name'], 'price': service['price']} for service in services_data],
        ensure_ascii=False
    )
    context = {
        'popular_services': popular_services,
        'total_services': len(services_data),
        'search_suggestions_json': search_json,
        'categories': CATEGORY_ORDER,
    }
    return render(request, 'authentication/home.html', context)


@customer_required
def services_view(request):
    services_data = _get_services_data()
    services_by_category = OrderedDict()
    for category in CATEGORY_ORDER:
        category_services = [
            service for service in services_data if service['category'].lower() == category.lower()
        ]
        if category_services:
            services_by_category[category] = category_services

    search_json = json.dumps(
        [{'name': service['name'], 'price': service['price']} for service in services_data],
        ensure_ascii=False
    )

    context = {
        'services_by_category': services_by_category,
        'search_suggestions_json': search_json,
    }
    
    return render(request, 'authentication/services.html', context)


@customer_required
def search_results_view(request):
    query = request.GET.get('q', '').strip()
    
    services_data = _get_services_data()
    if query:
        filtered_services = [
            service for service in services_data
            if query.lower() in service['name'].lower()
        ]
    else:
        filtered_services = services_data

    search_json = json.dumps(
        [{'name': service['name'], 'price': service['price']} for service in services_data],
        ensure_ascii=False
    )
    
    context = {
        'query': query,
        'services': filtered_services,
        'results_count': len(filtered_services),
        'search_suggestions_json': search_json,
    }
    
    return render(request, 'authentication/search_results.html', context)


def logout_view(request):
    customer_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def _get_booked_time_slots_for_customer(customer_id, exclude_appointment_id=None):
    """Get booked time slots for a customer grouped by date"""
    if exclude_appointment_id:
        sql = """
            SELECT Date, Time
            FROM APPOINTMENT
            WHERE Customer_ID = %s
            AND Appointment_ID != %s
            AND Status IN ('confirmed', 'scheduled')
            ORDER BY Date, Time
        """
        params = [customer_id, exclude_appointment_id]
    else:
        sql = """
            SELECT Date, Time
            FROM APPOINTMENT
            WHERE Customer_ID = %s
            AND Status IN ('confirmed', 'scheduled')
            ORDER BY Date, Time
        """
        params = [customer_id]
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
    except OperationalError:
        return {}
    
    # Group by date
    booked_slots = {}
    for row in rows:
        date_str = str(row[0])  # Date as string (YYYY-MM-DD format)
        time_obj = row[1]  # Time object
        
        # Normalize time to match display format used in booking template
        # Booking template uses: '11:00 AM', '1:00 PM' (no leading zero for single-digit hours)
        if isinstance(time_obj, time):
            # Format: "11:00 AM" or "1:00 PM" (remove leading zero from hour)
            hour = time_obj.hour
            minute = time_obj.minute
            am_pm = 'AM' if hour < 12 else 'PM'
            hour_12 = hour if hour <= 12 else hour - 12
            if hour_12 == 0:
                hour_12 = 12
            # Remove leading zero from hour to match template format
            time_str = f"{hour_12}:{minute:02d} {am_pm}"
        elif isinstance(time_obj, str):
            # If it's already a string, try to normalize it
            try:
                # Handle formats like "11:00:00" or "11:00 AM" or "01:00 PM"
                if ':' in time_obj:
                    time_part = time_obj.split()[0] if ' ' in time_obj else time_obj
                    parts = time_part.split(':')
                    hour = int(parts[0])
                    minute = int(parts[1]) if len(parts) > 1 else 0
                    am_pm = 'AM' if hour < 12 else 'PM'
                    hour_12 = hour if hour <= 12 else hour - 12
                    if hour_12 == 0:
                        hour_12 = 12
                    time_str = f"{hour_12}:{minute:02d} {am_pm}"
                else:
                    time_str = time_obj
            except:
                time_str = str(time_obj)
        else:
            time_str = str(time_obj)
        
        if date_str not in booked_slots:
            booked_slots[date_str] = []
        booked_slots[date_str].append(time_str)
    
    return booked_slots


@customer_required
def booking_view(request):
    service_name = request.GET.get('service', '')
    service_price = request.GET.get('price', '')
    service_description = request.GET.get('description', '')
    
    if request.method == 'POST':
        from django.http import JsonResponse
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        
        if booking_date and booking_time:
            # Store booking data in session instead of creating appointment
            request.session['pending_booking'] = {
                'service_name': service_name,
                'service_price': service_price,
                'service_description': service_description,
                'booking_date': booking_date,
                'booking_time': booking_time,
            }
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Please select both date and time'})
    
    # Get booked time slots for this customer
    booked_slots = _get_booked_time_slots_for_customer(request.customer.Customer_ID)
    
    # Get service image
    service_image = _get_service_image(service_name)
    
    context = {
        'service_name': service_name,
        'service_price': service_price,
        'service_description': service_description,
        'service_image': service_image,
        'booked_slots': json.dumps(booked_slots),  # Pass as JSON for JavaScript
    }
    return render(request, 'authentication/booking.html', context)


@customer_required
def confirm_booking_view(request):
    from django.http import JsonResponse
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE APPOINTMENT
                    SET Status = 'confirmed'
                    WHERE Appointment_ID = %s AND Customer_ID = %s
                    """,
                    [booking_id, request.customer.Customer_ID]
                )
                if cursor.rowcount:
                    return JsonResponse({'success': True})
        except OperationalError as exc:
            return JsonResponse({'success': False, 'error': 'Unable to confirm booking right now.'})
        return JsonResponse({'success': False, 'error': 'Booking not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@customer_required
def booking_confirmation_view(request, receipt_id):
    """Display booking confirmation with receipt details"""
    try:
        with connection.cursor() as cursor:
            # Fetch receipt and related data
            cursor.execute("""
                SELECT r.Receipt_ID, r.Receipt_Number, r.Amount, r.Receipt_Date, r.created_at,
                       s.ServiceName,
                       a.Date, a.Time, a.Status,
                       p.Method,
                       c.First_Name, c.Last_Name, c.Mobile_No
                FROM RECEIPTS r
                LEFT JOIN APPOINTMENT a ON r.Appointment_ID = a.Appointment_ID
                LEFT JOIN SALES s ON r.Sales_ID = s.Sales_ID
                LEFT JOIN PAYMENT p ON a.Payment_ID = p.Payment_ID
                LEFT JOIN CUSTOMER c ON r.Customer_ID = c.Customer_ID
                WHERE r.Receipt_ID = %s AND r.Customer_ID = %s
            """, [receipt_id, request.customer.Customer_ID])
            row = cursor.fetchone()
            
            if not row:
                messages.error(request, 'Receipt not found.')
                return redirect('my_bookings')
            
            # Format appointment date
            appointment_date = row[6]
            if appointment_date:
                try:
                    if isinstance(appointment_date, date):
                        formatted_date = appointment_date.strftime('%A, %B %d, %Y')
                    else:
                        formatted_date = datetime.strptime(str(appointment_date), '%Y-%m-%d').strftime('%A, %B %d, %Y')
                except:
                    formatted_date = str(appointment_date)
            else:
                formatted_date = 'N/A'
            
            # Format appointment time
            appointment_time = row[7]
            if appointment_time:
                if isinstance(appointment_time, time):
                    formatted_time = appointment_time.strftime('%I:%M %p').lstrip('0')
                else:
                    try:
                        time_obj = datetime.strptime(str(appointment_time), '%H:%M:%S').time()
                        formatted_time = time_obj.strftime('%I:%M %p').lstrip('0')
                    except:
                        formatted_time = str(appointment_time)
            else:
                formatted_time = 'N/A'
            
            # Format payment method
            payment_method = row[9] or 'Card'
            if payment_method:
                payment_method_display = payment_method.replace('_', ' ').title()
            else:
                payment_method_display = 'Card'
            
            # Format receipt date
            receipt_date = row[3]
            if receipt_date:
                try:
                    if isinstance(receipt_date, date):
                        formatted_receipt_date = receipt_date.strftime('%B %d, %Y')
                    else:
                        formatted_receipt_date = datetime.strptime(str(receipt_date), '%Y-%m-%d').strftime('%B %d, %Y')
                except:
                    formatted_receipt_date = str(receipt_date)
            else:
                formatted_receipt_date = datetime.now().strftime('%B %d, %Y')
            
            context = {
                'receipt_id': row[0],
                'receipt_number': row[1] or f'RCP{str(row[0]).zfill(3)}',
                'amount': _format_price(row[2]),
                'service_name': row[5] or 'Service',
                'appointment_date': formatted_date,
                'appointment_time': formatted_time,
                'payment_method': payment_method_display,
                'receipt_date': formatted_receipt_date,
                'customer_name': f"{row[10]} {row[11]}" if row[10] and row[11] else 'Customer',
                'customer_mobile': row[12] or '',
            }
            
            return render(request, 'authentication/booking_confirmation.html', context)
            
    except Exception as e:
        messages.error(request, f'Error loading receipt: {str(e)}')
        return redirect('my_bookings')


@customer_required
def my_bookings_view(request):
    bookings = _fetch_appointments_for_customer(request.customer.Customer_ID)
    context = {
        'bookings': bookings,
    }
    return render(request, 'authentication/my_bookings.html', context)


@customer_required
def delete_booking_view(request):
    from django.http import JsonResponse
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM APPOINTMENT WHERE Appointment_ID = %s AND Customer_ID = %s",
                    [booking_id, request.customer.Customer_ID]
                )
                if cursor.rowcount:
                    return JsonResponse({'success': True})
        except OperationalError as exc:
            return JsonResponse({'success': False, 'error': 'Unable to delete booking at the moment.'})
        return JsonResponse({'success': False, 'error': 'Booking not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@customer_required
def edit_booking_view(request):
    """Display edit booking form with pre-filled data"""
    booking_id = request.GET.get('id')
    if not booking_id:
        messages.error(request, 'Booking ID is required.')
        return redirect('my_bookings')
    
    try:
        with connection.cursor() as cursor:
            # Fetch booking details
            cursor.execute("""
                SELECT a.Appointment_ID,
                       COALESCE(s.ServiceName, 'Scheduled Service') AS service_name,
                       COALESCE(s.ServiceName, 'Scheduled Service appointment') AS service_description,
                       COALESCE(p.Amount, 0) AS amount,
                       a.Date,
                       a.Time,
                       COALESCE(a.Status, 'scheduled') AS status
                FROM APPOINTMENT a
                LEFT JOIN SALES s ON a.Sales_ID = s.Sales_ID
                LEFT JOIN PAYMENT p ON a.Payment_ID = p.Payment_ID
                WHERE a.Appointment_ID = %s AND a.Customer_ID = %s
            """, [booking_id, request.customer.Customer_ID])
            row = cursor.fetchone()
            
            if not row:
                messages.error(request, 'Booking not found.')
                return redirect('my_bookings')
            
            booking_date = row[4]
            booking_time = row[5]
            
            # Ensure booking_date is a date object (not datetime)
            if isinstance(booking_date, datetime):
                booking_date = booking_date.date()
            elif isinstance(booking_date, str):
                try:
                    booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
                except:
                    booking_date = datetime.strptime(booking_date.split()[0], '%Y-%m-%d').date()
            
            # Check if booking can be edited (more than 24 hours before)
            # Parse booking time
            if isinstance(booking_time, time):
                booking_time_obj = booking_time
            else:
                try:
                    booking_time_obj = datetime.strptime(str(booking_time), '%H:%M:%S').time()
                except:
                    try:
                        booking_time_obj = datetime.strptime(str(booking_time), '%H:%M').time()
                    except:
                        booking_time_obj = time(12, 0)  # Default to noon if parsing fails
            
            appointment_datetime = datetime.combine(booking_date, booking_time_obj)
            current_datetime = datetime.now()
            time_diff = appointment_datetime - current_datetime
            
            if time_diff.total_seconds() < 86400:  # Less than 24 hours (86400 seconds)
                messages.error(request, 'You can only modify bookings that are more than 24 hours away.')
                return redirect('my_bookings')
            
            # Format booking time for display
            if isinstance(booking_time, time):
                booking_time_str = booking_time.strftime('%I:%M %p').lstrip('0')
            elif isinstance(booking_time, str):
                try:
                    time_obj = datetime.strptime(booking_time, '%H:%M:%S').time()
                    booking_time_str = time_obj.strftime('%I:%M %p').lstrip('0')
                except:
                    booking_time_str = booking_time
            else:
                booking_time_str = str(booking_time)
            
            # Calculate minimum selectable date (next day after current booking date)
            # Since we've already verified the booking is more than 24 hours away,
            # we can safely allow the next day (Dec 3 if booking is Dec 2)
            min_date = booking_date + timedelta(days=1)
            
            # Get booked time slots for this customer (excluding current booking)
            booked_slots = _get_booked_time_slots_for_customer(request.customer.Customer_ID, exclude_appointment_id=booking_id)
            
            context = {
                'booking_id': booking_id,
                'service_name': row[1],
                'service_description': row[2],
                'service_price': _format_price(row[3]),
                'current_date': booking_date.strftime('%Y-%m-%d'),
                'current_time': booking_time_str,
                'min_date': min_date.strftime('%Y-%m-%d'),
                'booked_slots': json.dumps(booked_slots),
            }
            
            return render(request, 'authentication/edit_booking.html', context)
            
    except Exception as e:
        messages.error(request, f'Error loading booking: {str(e)}')
        return redirect('my_bookings')


@customer_required
@csrf_protect
def update_booking_view(request):
    """Update booking date and time"""
    from django.http import JsonResponse
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        new_date = request.POST.get('booking_date')
        new_time = request.POST.get('booking_time')
        
        if not booking_id or not new_date or not new_time:
            return JsonResponse({'success': False, 'error': 'Please provide all required fields.'})
        
        try:
            with connection.cursor() as cursor:
                # Verify booking belongs to customer and check 24-hour restriction
                cursor.execute("""
                    SELECT Date, Time
                    FROM APPOINTMENT
                    WHERE Appointment_ID = %s AND Customer_ID = %s
                """, [booking_id, request.customer.Customer_ID])
                row = cursor.fetchone()
                
                if not row:
                    return JsonResponse({'success': False, 'error': 'Booking not found.'})
                
                old_date = row[0]
                old_time = row[1]
                
                # Parse old time
                if isinstance(old_time, time):
                    old_time_obj = old_time
                else:
                    try:
                        old_time_obj = datetime.strptime(str(old_time), '%H:%M:%S').time()
                    except:
                        old_time_obj = datetime.strptime(str(old_time), '%H:%M').time()
                
                # Check if booking can be edited (more than 24 hours before)
                appointment_datetime = datetime.combine(old_date, old_time_obj)
                current_datetime = datetime.now()
                time_diff = appointment_datetime - current_datetime
                
                if time_diff.total_seconds() < 86400:  # Less than 24 hours
                    return JsonResponse({'success': False, 'error': 'You can only modify bookings that are more than 24 hours away.'})
                
                # Validate new date is after current booking date
                new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
                if new_date_obj <= old_date:
                    return JsonResponse({'success': False, 'error': 'You can only select dates after the current booking date.'})
                
                # Normalize new time
                normalized_time = _normalize_time_slot(new_time)
                
                # Update booking
                cursor.execute("""
                    UPDATE APPOINTMENT
                    SET Date = %s, Time = %s
                    WHERE Appointment_ID = %s AND Customer_ID = %s
                """, [new_date, normalized_time, booking_id, request.customer.Customer_ID])
                
                if cursor.rowcount:
                    return JsonResponse({'success': True, 'message': 'Booking updated successfully!'})
                else:
                    return JsonResponse({'success': False, 'error': 'Failed to update booking.'})
                    
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error updating booking: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@customer_required
@customer_required
def profile_view(request):
    saved_addresses = _fetch_addresses_for_customer(request.customer)
    bookings = _fetch_appointments_for_customer(request.customer.Customer_ID)[:5]
    
    context = {
        'customer': request.customer,
        'saved_addresses': saved_addresses,
        'recent_bookings': bookings,
        'profile_display_name': _get_profile_display_name(request.customer),
    }
    return render(request, 'authentication/profile.html', context)


@customer_required
def my_receipts_view(request):
    receipts = _fetch_receipts_for_customer(request.customer.Customer_ID)
    
    context = {
        'receipts': receipts,
    }
    return render(request, 'authentication/my_receipts.html', context)


@customer_required
def delete_receipt_view(request):
    """Delete a receipt from the database"""
    if request.method == 'POST':
        receipt_id = request.POST.get('receipt_id')
        
        if not receipt_id:
            return JsonResponse({'success': False, 'error': 'Receipt ID is required.'})
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Verify receipt belongs to customer
                    cursor.execute("""
                        SELECT Customer_ID FROM RECEIPTS WHERE Receipt_ID = %s
                    """, [receipt_id])
                    row = cursor.fetchone()
                    
                    if not row or row[0] != request.customer.Customer_ID:
                        return JsonResponse({'success': False, 'error': 'Receipt not found or access denied.'})
                    
                    # Delete the receipt
                    cursor.execute("""
                        DELETE FROM RECEIPTS WHERE Receipt_ID = %s
                    """, [receipt_id])
                    
                    if cursor.rowcount > 0:
                        return JsonResponse({'success': True, 'message': 'Receipt deleted successfully.'})
                    else:
                        return JsonResponse({'success': False, 'error': 'Receipt not found.'})
        except OperationalError as exc:
            return JsonResponse({'success': False, 'error': 'Unable to delete receipt. Please try again.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@customer_required
def view_receipt_pdf(request, receipt_id):
    """Generate and display PDF receipt"""
    try:
        with connection.cursor() as cursor:
            # Fetch receipt and related data
            cursor.execute("""
                SELECT r.Receipt_ID, r.Receipt_Number, r.Amount, r.Receipt_Date, r.created_at,
                       s.ServiceName,
                       a.Date, a.Time, a.Status,
                       p.Method,
                       c.First_Name, c.Last_Name, c.Mobile_No, c.Address
                FROM RECEIPTS r
                LEFT JOIN APPOINTMENT a ON r.Appointment_ID = a.Appointment_ID
                LEFT JOIN SALES s ON r.Sales_ID = s.Sales_ID
                LEFT JOIN PAYMENT p ON a.Payment_ID = p.Payment_ID
                LEFT JOIN CUSTOMER c ON r.Customer_ID = c.Customer_ID
                WHERE r.Receipt_ID = %s AND r.Customer_ID = %s
            """, [receipt_id, request.customer.Customer_ID])
            row = cursor.fetchone()
            
            if not row:
                return HttpResponse('Receipt not found.', status=404)
            
            # Extract data
            receipt_number = row[1] or f'RCP{str(row[0]).zfill(3)}'
            amount = row[2]
            service_name = row[5] or 'Service'
            appointment_date = row[6]
            appointment_time = row[7]
            payment_method = row[9] or 'Card'
            customer_name = f"{row[10]} {row[11]}" if row[10] and row[11] else 'Customer'
            customer_mobile = row[12] or ''
            customer_address = row[13] or ''
            receipt_date = row[3] or datetime.now().date()
            
            # Format dates
            if isinstance(appointment_date, date):
                formatted_appointment_date = appointment_date.strftime('%A, %B %d, %Y')
            else:
                try:
                    formatted_appointment_date = datetime.strptime(str(appointment_date), '%Y-%m-%d').strftime('%A, %B %d, %Y')
                except:
                    formatted_appointment_date = str(appointment_date)
            
            # Format time
            if isinstance(appointment_time, time):
                formatted_time = appointment_time.strftime('%I:%M %p').lstrip('0')
            else:
                try:
                    time_obj = datetime.strptime(str(appointment_time), '%H:%M:%S').time()
                    formatted_time = time_obj.strftime('%I:%M %p').lstrip('0')
                except:
                    formatted_time = str(appointment_time)
            
            # Format receipt date
            if isinstance(receipt_date, date):
                formatted_receipt_date = receipt_date.strftime('%B %d, %Y')
            else:
                try:
                    formatted_receipt_date = datetime.strptime(str(receipt_date), '%Y-%m-%d').strftime('%B %d, %Y')
                except:
                    formatted_receipt_date = datetime.now().strftime('%B %d, %Y')
            
            # Format payment method
            payment_method_display = payment_method.replace('_', ' ').title()
            
            # Create PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Receipt_{receipt_number}.pdf"'
            
            # Create document
            doc = SimpleDocTemplate(response, pagesize=letter,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Container for PDF elements
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=colors.HexColor('#603D44'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#603D44'),
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6
            )
            
            # Title
            elements.append(Paragraph("GLAMORA", title_style))
            elements.append(Paragraph("RECEIPT", ParagraphStyle(
                'ReceiptLabel',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceAfter=30
            )))
            
            # Receipt Number
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph(f"Receipt Number: {receipt_number}", ParagraphStyle(
                'ReceiptNumber',
                parent=styles['Normal'],
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=20,
                fontName='Helvetica-Bold'
            )))
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Receipt Details Table
            receipt_data = []
            
            # Add customer info if available
            if customer_name:
                receipt_data.append(['Customer Name:', customer_name])
            receipt_data.append(['Service:', service_name])
            receipt_data.append(['Appointment Date:', formatted_appointment_date])
            receipt_data.append(['Appointment Time:', formatted_time])
            receipt_data.append(['Payment Method:', payment_method_display])
            receipt_data.append(['Receipt Date:', formatted_receipt_date])
            if customer_mobile:
                receipt_data.append(['Mobile:', customer_mobile])
            if customer_address:
                # Use Paragraph for address to handle wrapping
                address_para = Paragraph(customer_address, ParagraphStyle(
                    'AddressStyle',
                    parent=styles['Normal'],
                    fontSize=11,
                    fontName='Helvetica',
                    leading=13,
                    wordWrap='LTR'
                ))
                receipt_data.append(['Address:', address_para])
            
            # Count data rows (before separator and total)
            data_row_count = len(receipt_data)
            
            # Add total amount
            receipt_data.append(['', ''])
            receipt_data.append(['TOTAL AMOUNT:', f'${amount:,.2f}'])
            
            receipt_table = Table(receipt_data, colWidths=[2.5*inch, 3.5*inch])
            receipt_table.setStyle(TableStyle([
                # Gray background only for data rows (left column)
                ('BACKGROUND', (0, 0), (0, data_row_count - 1), colors.HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, data_row_count - 1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, data_row_count - 1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, data_row_count - 1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                # Grid lines only for data rows
                ('GRID', (0, 0), (-1, data_row_count - 1), 1, colors.grey),
                # Separator line before total
                ('LINEBELOW', (0, data_row_count), (-1, data_row_count), 2, colors.HexColor('#603D44')),
                # Total row styling
                ('FONTSIZE', (0, -1), (-1, -1), 14),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TOPPADDING', (0, -1), (-1, -1), 15),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 15),
            ]))
            
            elements.append(receipt_table)
            elements.append(Spacer(1, 0.5*inch))
            
            # Footer
            elements.append(Paragraph("Thank you for choosing GLAMORA!", ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey,
                spaceBefore=20
            )))
            
            # Build PDF
            doc.build(elements)
            
            return response
            
    except Exception as e:
        return HttpResponse(f'Error generating PDF: {str(e)}', status=500)


@customer_required
def saved_addresses_view(request):
    addresses = _fetch_addresses_for_customer(request.customer)
    context = {
        'addresses': addresses,
    }
    return render(request, 'authentication/saved_addresses.html', context)


@customer_required
def profile_settings_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        mobile_no = ''.join(filter(str.isdigit, request.POST.get('mobile_no', '').strip()))
        
        if not first_name or not last_name or not mobile_no:
            messages.error(request, 'First name, last name, and mobile number are required.')
            return redirect('profile_settings')
        
        customer = request.customer
        try:
            with transaction.atomic():
                db_executor = connection.cursor()
                
                if mobile_no != customer.Mobile_No:
                    db_executor.execute("SELECT Customer_ID FROM CUSTOMER WHERE Mobile_No = %s", [mobile_no])
                    if db_executor.fetchone():
                        messages.error(request, 'Mobile number already exists. Please use another number.')
                        return redirect('profile_settings')
                
                db_executor.execute("""
                    UPDATE CUSTOMER
                    SET First_Name = %s,
                        Last_Name = %s,
                        Mobile_No = %s,
                        updated_at = NOW()
                    WHERE Customer_ID = %s
                """, [first_name, last_name, mobile_no, customer.Customer_ID])
        except Exception as e:
            messages.error(request, 'Failed to update profile. Please try again.')
            return redirect('profile_settings')
        
        # Update session data
        customer.First_Name = first_name
        customer.Last_Name = last_name
        customer.Mobile_No = mobile_no
        request.session['customer_mobile'] = mobile_no
        request.session['customer_name'] = f"{first_name} {last_name}".strip()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    context = {
        'customer': request.customer,
        'first_name': request.customer.First_Name,
        'last_name': request.customer.Last_Name,
        'mobile_no': request.customer.Mobile_No,
    }
    return render(request, 'authentication/profile_settings.html', context)


@customer_required
def change_password_view(request):
    from django.http import JsonResponse
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        customer = request.customer
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'error': 'New passwords do not match.'})
        if len(new_password) < 6:
            return JsonResponse({'success': False, 'error': 'Password must be at least 6 characters.'})
        
        try:
            with transaction.atomic():
                db_executor = connection.cursor()
                db_executor.execute("SELECT Password FROM CUSTOMER WHERE Customer_ID = %s", [customer.Customer_ID])
                row = db_executor.fetchone()
                if not row or row[0] != old_password:
                    return JsonResponse({'success': False, 'error': 'Current password is incorrect.'})
                
                db_executor.execute("""
                    UPDATE CUSTOMER
                    SET Password = %s,
                        updated_at = NOW()
                    WHERE Customer_ID = %s
                """, [new_password, customer.Customer_ID])
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Failed to change password. Please try again.'})
        
        customer.Password = new_password
        return JsonResponse({'success': True, 'message': 'Password changed successfully.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request.'})


@customer_required
def payment_view(request):
    pending_booking = request.session.get('pending_booking')
    if not pending_booking:
        messages.error(request, 'No booking found. Please start a new booking.')
        return redirect('services')
    
    if request.method == 'POST':
        raw_card_number = request.POST.get('raw_card_number', '').strip()
        card_number = raw_card_number if raw_card_number else request.POST.get('card_number', '').strip()
        card_holder = request.POST.get('card_holder', '').strip()
        expiry_date = request.POST.get('expiry_date', '').strip()
        cvv = request.POST.get('cvv', '').strip()
        
        if not card_number or not card_holder or not expiry_date or not cvv:
            messages.error(request, 'Please fill all card details.')
            try:
                booking_date_obj = datetime.strptime(pending_booking['booking_date'], '%Y-%m-%d').date()
                pending_booking['formatted_date'] = booking_date_obj.strftime('%A, %B %d, %Y')
            except:
                pending_booking['formatted_date'] = pending_booking['booking_date']
            return render(request, 'authentication/payment.html', {
                'pending_booking': pending_booking,
            })
        
        card_type = request.POST.get('card_type', '').strip()
        if not card_type:
            messages.error(request, 'Please select a card type (Credit Card or Debit Card).')
            try:
                booking_date_obj = datetime.strptime(pending_booking['booking_date'], '%Y-%m-%d').date()
                pending_booking['formatted_date'] = booking_date_obj.strftime('%A, %B %d, %Y')
            except:
                pending_booking['formatted_date'] = pending_booking['booking_date']
            return render(request, 'authentication/payment.html', {
                'pending_booking': pending_booking,
            })
        
        if card_type == 'credit':
            payment_method_db = 'credit_card'
        elif card_type == 'debit':
            payment_method_db = 'debit_card'
        else:
            payment_method_db = 'card'
        
        clean_card_number = card_number.replace(' ', '').replace('*', '').replace('-', '') if card_number else ''
        card_last_four = clean_card_number[-4:] if len(clean_card_number) >= 4 else clean_card_number
        
        request.session['payment_data'] = {
            'method': payment_method_db,
            'card_number': card_last_four,
            'card_holder': card_holder,
            'expiry_date': expiry_date,
        }
        
        request.session.modified = True
        
        try:
            booking_date_obj = datetime.strptime(pending_booking['booking_date'], '%Y-%m-%d').date()
            pending_booking['formatted_date'] = booking_date_obj.strftime('%A, %B %d, %Y')
        except:
            pending_booking['formatted_date'] = pending_booking['booking_date']
        
        payment_method_display = payment_method_db.replace('_', ' ').title()
        payment_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
        
        return render(request, 'authentication/payment_confirmation.html', {
            'pending_booking': pending_booking,
            'payment_data': request.session['payment_data'],
            'payment_method_display': payment_method_display,
            'payment_date': payment_date,
        })
    
    try:
        booking_date_obj = datetime.strptime(pending_booking['booking_date'], '%Y-%m-%d').date()
        pending_booking['formatted_date'] = booking_date_obj.strftime('%A, %B %d, %Y')
    except:
        pending_booking['formatted_date'] = pending_booking['booking_date']
    
    context = {
        'pending_booking': pending_booking,
    }
    return render(request, 'authentication/payment.html', context)


@customer_required
def address_view(request):
    # Check if there's pending booking and payment data
    pending_booking = request.session.get('pending_booking')
    payment_data = request.session.get('payment_data')
    
    if not pending_booking:
        messages.error(request, 'No booking found. Please start a new booking.')
        return redirect('services')
    
    if not payment_data:
        messages.error(request, 'Please complete payment first.')
        return redirect('payment')
    
    # Format date for display
    try:
        booking_date_obj = datetime.strptime(pending_booking['booking_date'], '%Y-%m-%d').date()
        pending_booking['formatted_date'] = booking_date_obj.strftime('%A, %B %d, %Y')
    except:
        pending_booking['formatted_date'] = pending_booking['booking_date']
    
    # Fetch saved addresses
    saved_addresses = _fetch_addresses_for_customer(request.customer)
    
    if request.method == 'POST':
        use_saved_address = request.POST.get('use_saved_address')
        selected_address_id = request.POST.get('selected_address_id')
        
        # If using saved address, get the selected address
        if use_saved_address == 'yes' and selected_address_id:
            try:
                addr_id = int(selected_address_id)
                if addr_id < len(saved_addresses):
                    selected_addr = saved_addresses[addr_id]
                    full_address = selected_addr.get('full_address', '')
                    if not full_address:
                        # Reconstruct from parts
                        full_address = selected_addr.get('address_line1', '')
                        if selected_addr.get('address_line2'):
                            full_address += f", {selected_addr['address_line2']}"
                        full_address += f", {selected_addr.get('city', '')}, {selected_addr.get('state', '')} {selected_addr.get('zip_code', '')}"
                        if selected_addr.get('country'):
                            full_address += f", {selected_addr['country']}"
                else:
                    messages.error(request, 'Selected address not found.')
                    return render(request, 'authentication/address.html', {
                        'pending_booking': pending_booking,
                        'payment_data': payment_data,
                        'customer': request.customer,
                        'saved_addresses': saved_addresses,
                    })
            except (ValueError, IndexError):
                messages.error(request, 'Invalid address selection.')
                return render(request, 'authentication/address.html', {
                    'pending_booking': pending_booking,
                    'payment_data': payment_data,
                    'customer': request.customer,
                    'saved_addresses': saved_addresses,
                })
        else:
            address_line1 = request.POST.get('address_line1', '').strip()
            address_line2 = request.POST.get('address_line2', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            zip_code = request.POST.get('zip_code', '').strip()
            country = request.POST.get('country', '').strip()
            
            if not address_line1 or not city or not state or not zip_code:
                messages.error(request, 'Please fill all required address fields.')
                return render(request, 'authentication/address.html', {
                    'pending_booking': pending_booking,
                    'payment_data': payment_data,
                    'customer': request.customer,
                    'saved_addresses': saved_addresses,
                })
            
            # Combine address
            full_address = address_line1
            if address_line2:
                full_address += f", {address_line2}"
            full_address += f", {city}, {state} {zip_code}"
            if country:
                full_address += f", {country}"
        
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Get service ID
                    cursor.execute(
                        "SELECT Service_ID FROM SERVICE WHERE ServiceName = %s LIMIT 1",
                        [pending_booking['service_name']]
                    )
                    row = cursor.fetchone()
                    service_id = row[0] if row else None
                    
                    # Extract price from string (remove $ and commas)
                    price_str = pending_booking['service_price'].replace('$', '').replace(',', '')
                    try:
                        price_amount = Decimal(price_str)
                    except:
                        price_amount = Decimal('0.00')
                    
                    # Get payment method (database column now supports up to 50 characters)
                    payment_method = (payment_data.get('method', 'card') or 'card').lower().strip()
                    
                    # Create payment record
                    cursor.execute("""
                        INSERT INTO PAYMENT (Appointment_ID, Method, Amount, Date, Status)
                        VALUES (NULL, %s, %s, %s, 'completed')
                    """, [payment_method, price_amount, pending_booking['booking_date']])
                    payment_id = cursor.lastrowid
                    
                    # Create sales record
                    cursor.execute("""
                        INSERT INTO SALES (Payment_ID, Employee_ID, Admin_ID, Service_ID, ServiceName, Date, Receipt)
                        VALUES (%s, %s, %s, %s, %s, %s, NULL)
                    """, [payment_id, 1, 1, service_id, pending_booking['service_name'], pending_booking['booking_date']])
                    sales_id = cursor.lastrowid
                    
                    # Create appointment record
                    cursor.execute("""
                        INSERT INTO APPOINTMENT (
                            Customer_ID, Employee_ID, Payment_ID, Admin_ID, Sales_ID,
                            Date, Time, Status, Receipt
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL)
                    """, [
                        request.customer.Customer_ID,
                        1,
                        payment_id,
                        1,
                        sales_id,
                        pending_booking['booking_date'],
                        _normalize_time_slot(pending_booking['booking_time']),
                        'confirmed'
                    ])
                    appointment_id = cursor.lastrowid
                    
                    # Update customer address if save_address is checked (plain text, not JSON)
                    save_address = request.POST.get('save_address') == 'on'
                    if save_address and use_saved_address != 'yes':
                        # Save address as plain text (not JSON)
                        cursor.execute("""
                            UPDATE CUSTOMER
                            SET Address = %s, updated_at = NOW()
                            WHERE Customer_ID = %s
                        """, [full_address, request.customer.Customer_ID])
                        
                        # Update customer object in session
                        request.customer.Address = full_address
                        messages.success(request, 'Address saved successfully!')
                    
                    # Update payment with appointment ID
                    cursor.execute("""
                        UPDATE PAYMENT
                        SET Appointment_ID = %s
                        WHERE Payment_ID = %s
                    """, [appointment_id, payment_id])
                    
                    # Create receipt record
                    receipt_date = datetime.now().date()
                    
                    # Generate receipt number (format: RCPXXX where XXX is an incrementing number)
                    # Get the highest existing receipt number
                    cursor.execute("""
                        SELECT Receipt_Number FROM RECEIPTS 
                        WHERE Receipt_Number LIKE 'RCP%' 
                        ORDER BY CAST(SUBSTRING(Receipt_Number, 4) AS UNSIGNED) DESC 
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    
                    if row and row[0]:
                        # Extract the numeric part and increment
                        existing_number = row[0]
                        try:
                            # Extract number after "RCP" prefix
                            numeric_part = int(existing_number[3:])
                            next_number = numeric_part + 1
                        except (ValueError, IndexError):
                            # If parsing fails, start from 1
                            next_number = 1
                    else:
                        # No existing receipts, start from 1
                        next_number = 1
                    
                    # Format as RCPXXX (3 digits minimum, can be more if needed)
                    receipt_number = f"RCP{str(next_number).zfill(3)}"
                    
                    cursor.execute("""
                        INSERT INTO RECEIPTS (Customer_ID, Appointment_ID, Sales_ID, Amount, Receipt_Date, Receipt_Number, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, [
                        request.customer.Customer_ID,
                        appointment_id,
                        sales_id,
                        price_amount,
                        receipt_date,
                        receipt_number
                    ])
                    receipt_id = cursor.lastrowid
                    
                    # Update SALES table with Receipt_ID
                    cursor.execute("""
                        UPDATE SALES
                        SET Receipt = %s
                        WHERE Sales_ID = %s
                    """, [receipt_id, sales_id])
                    
                    # Update APPOINTMENT table with Receipt_Number (string format like RCP001)
                    cursor.execute("""
                        UPDATE APPOINTMENT
                        SET Receipt = %s
                        WHERE Appointment_ID = %s
                    """, [receipt_number, appointment_id])
                    
            # Clear session data
            del request.session['pending_booking']
            del request.session['payment_data']
            
            # Redirect to booking confirmation page with receipt ID
            return redirect(reverse('booking_confirmation', args=[receipt_id]))
            
        except OperationalError:
            messages.error(request, 'Unable to complete booking. Please try again.')
            saved_addresses = _fetch_addresses_for_customer(request.customer)
            return render(request, 'authentication/address.html', {
                'pending_booking': pending_booking,
                'payment_data': payment_data,
                'customer': request.customer,
                'saved_addresses': saved_addresses,
            })
    
    context = {
        'pending_booking': pending_booking,
        'payment_data': payment_data,
        'customer': request.customer,
        'saved_addresses': saved_addresses,
    }
    return render(request, 'authentication/address.html', context)


# ============================================
# ADMIN VIEWS
# ============================================

@admin_required
def admin_home_view(request):
    """Admin homepage with dashboard statistics"""
    try:
        with connection.cursor() as cursor:
            # Get total customers
            cursor.execute("SELECT COUNT(*) FROM CUSTOMER")
            total_customers = cursor.fetchone()[0]
            
            # Get total appointments
            cursor.execute("SELECT COUNT(*) FROM APPOINTMENT")
            total_appointments = cursor.fetchone()[0]
            
            # Get total sales - same calculation as sales management page
            cursor.execute("""
                SELECT COALESCE(SUM(p.Amount), 0)
                FROM SALES s
                LEFT JOIN PAYMENT p ON s.Payment_ID = p.Payment_ID
                WHERE p.Amount IS NOT NULL
            """)
            total_sales_result = cursor.fetchone()[0]
            total_sales = float(total_sales_result) if total_sales_result else 0.00
            
            # Get today's appointments
            cursor.execute("SELECT COUNT(*) FROM APPOINTMENT WHERE Date = CURDATE()")
            today_appointments = cursor.fetchone()[0]
            
            # Get recent appointments
            cursor.execute("""
                SELECT a.Appointment_ID, a.Date, a.Time, a.Status,
                       c.First_Name, c.Last_Name, c.Mobile_No,
                       s.ServiceName
                FROM APPOINTMENT a
                LEFT JOIN CUSTOMER c ON a.Customer_ID = c.Customer_ID
                LEFT JOIN SALES s ON a.Sales_ID = s.Sales_ID
                ORDER BY a.Date DESC, a.Time DESC
                LIMIT 10
            """)
            recent_appointments = cursor.fetchall()
            
            appointments_list = []
            for row in recent_appointments:
                appointments_list.append({
                    'id': row[0],
                    'date': row[1],
                    'time': row[2],
                    'status': row[3],
                    'customer_name': f"{row[4]} {row[5]}" if row[4] and row[5] else 'N/A',
                    'mobile': row[6] or 'N/A',
                    'service': row[7] or 'N/A',
                })
    except OperationalError:
        total_customers = 0
        total_appointments = 0
        total_sales = 0.00
        today_appointments = 0
        appointments_list = []
    
    context = {
        'total_customers': total_customers,
        'total_appointments': total_appointments,
        'total_sales': total_sales,
        'today_appointments': today_appointments,
        'recent_appointments': appointments_list,
    }
    return render(request, 'authentication/admin_home.html', context)


@admin_required
def admin_services_view(request):
    """Admin services management page"""
    services = _get_services_data()
    context = {
        'services': services,
    }
    return render(request, 'authentication/admin_services.html', context)


@admin_required
def admin_users_view(request):
    """Admin users management page with tabs for Customers, Employees, and Admins"""
    tab = request.GET.get('tab', 'customers')
    
    try:
        with connection.cursor() as cursor:
            # Fetch Customers
            cursor.execute("""
                SELECT Customer_ID, First_Name, Last_Name, Mobile_No, Address, created_at
                FROM CUSTOMER
                ORDER BY created_at DESC
            """)
            customer_rows = cursor.fetchall()
            customers = []
            for row in customer_rows:
                customers.append({
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'mobile': row[3],
                    'address': row[4] or 'N/A',
                    'created_at': row[5],
                })
            
            # Fetch Employees
            cursor.execute("""
                SELECT Employee_ID, First_Name, Last_Name, Phone, Address, Skills, Rating, Availability, created_at
                FROM EMPLOYEE
                ORDER BY created_at DESC
            """)
            employee_rows = cursor.fetchall()
            employees = []
            for row in employee_rows:
                employees.append({
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'phone': row[3],
                    'address': row[4] or 'N/A',
                    'skills': row[5] or 'N/A',
                    'rating': float(row[6]) if row[6] else 0.0,
                    'availability': row[7] or 'available',
                    'created_at': row[8],
                })
            
            # Fetch Admins
            cursor.execute("""
                SELECT Admin_ID, First_Name, Last_Name, Mobile_No, Role, created_at
                FROM ADMIN
                ORDER BY created_at DESC
            """)
            admin_rows = cursor.fetchall()
            admins = []
            for row in admin_rows:
                admins.append({
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'mobile': row[3],
                    'role': row[4],
                    'created_at': row[5],
                })
    except OperationalError:
        customers = []
        employees = []
        admins = []
    
    context = {
        'customers': customers,
        'employees': employees,
        'admins': admins,
        'active_tab': tab,
    }
    return render(request, 'authentication/admin_users.html', context)


@admin_required
def admin_appointments_view(request):
    """Admin appointments management page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT a.Appointment_ID, a.Date, a.Time, a.Status, a.Receipt,
                       c.First_Name, c.Last_Name, c.Mobile_No,
                       s.ServiceName, p.Amount
                FROM APPOINTMENT a
                LEFT JOIN CUSTOMER c ON a.Customer_ID = c.Customer_ID
                LEFT JOIN SALES s ON a.Sales_ID = s.Sales_ID
                LEFT JOIN PAYMENT p ON a.Payment_ID = p.Payment_ID
                ORDER BY a.Date DESC, a.Time DESC
            """)
            rows = cursor.fetchall()
            
            appointments = []
            for row in rows:
                appointments.append({
                    'id': row[0],
                    'date': row[1],
                    'time': _format_time_slot(row[2]) if row[2] else 'N/A',
                    'status': row[3],
                    'receipt': row[4] or 'N/A',
                    'customer_name': f"{row[5]} {row[6]}" if row[5] and row[6] else 'N/A',
                    'mobile': row[7] or 'N/A',
                    'service': row[8] or 'N/A',
                    'amount': _format_price(row[9]) if row[9] else '$0.00',
                })
    except OperationalError:
        appointments = []
    
    context = {
        'appointments': appointments,
    }
    return render(request, 'authentication/admin_appointments.html', context)


@admin_required
def admin_sales_view(request):
    """Admin sales management page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT s.Sales_ID, s.Date, s.ServiceName,
                       c.First_Name, c.Last_Name,
                       p.Amount, p.Status,
                       r.Receipt_Number
                FROM SALES s
                LEFT JOIN APPOINTMENT a ON s.Sales_ID = a.Sales_ID
                LEFT JOIN CUSTOMER c ON a.Customer_ID = c.Customer_ID
                LEFT JOIN PAYMENT p ON s.Payment_ID = p.Payment_ID
                LEFT JOIN RECEIPTS r ON s.Receipt = r.Receipt_ID
                ORDER BY s.Date DESC, s.Sales_ID DESC
            """)
            rows = cursor.fetchall()
            
            sales = []
            total_revenue = Decimal('0.00')
            for row in rows:
                amount = Decimal(str(row[5])) if row[5] else Decimal('0.00')
                total_revenue += amount
                sales.append({
                    'id': row[0],
                    'date': row[1],
                    'service': row[2] or 'N/A',
                    'customer_name': f"{row[3]} {row[4]}" if row[3] and row[4] else 'N/A',
                    'amount': _format_price(row[5]) if row[5] else '$0.00',
                    'status': row[6] or 'N/A',
                    'receipt': row[7] or 'N/A',
                })
    except OperationalError:
        sales = []
        total_revenue = Decimal('0.00')
    
    context = {
        'sales': sales,
        'total_revenue': _format_price(total_revenue),
    }
    return render(request, 'authentication/admin_sales.html', context)


# ============================================
# SERVICE MANAGEMENT VIEWS
# ============================================

@admin_required
@csrf_protect
def admin_add_service_view(request):
    """Add new service"""
    if request.method == 'POST':
        try:
            service_name = request.POST.get('service_name')
            category = request.POST.get('category')
            description = request.POST.get('description', '')
            price = Decimal(request.POST.get('price', '0'))
            original_price = request.POST.get('original_price')
            original_price = Decimal(original_price) if original_price else None
            discount_label = request.POST.get('discount_label', '')
            is_active = request.POST.get('is_active') == 'on'
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO SERVICE (ServiceName, Category, Description, Price, Original_Price, Discount_Label, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [service_name, category, description, price, original_price, discount_label, is_active])
                
            messages.success(request, 'Service added successfully!')
            return redirect('admin_services')
        except Exception as e:
            messages.error(request, f'Error adding service: {str(e)}')
            return redirect('admin_services')
    return redirect('admin_services')


@admin_required
def admin_get_service_view(request, service_id):
    """Get service details for editing"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Service_ID, ServiceName, Category, Description, Price, Original_Price, Discount_Label, is_active
                FROM SERVICE WHERE Service_ID = %s
            """, [service_id])
            row = cursor.fetchone()
            
            if row:
                return JsonResponse({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'description': row[3] or '',
                    'price': float(row[4]),
                    'original_price': float(row[5]) if row[5] else None,
                    'discount_label': row[6] or '',
                    'is_active': bool(row[7]),
                })
    except Exception:
        pass
    return JsonResponse({'error': 'Service not found'}, status=404)


@admin_required
@csrf_protect
def admin_edit_service_view(request):
    """Edit existing service"""
    if request.method == 'POST':
        try:
            service_id = request.POST.get('service_id')
            service_name = request.POST.get('service_name')
            category = request.POST.get('category')
            description = request.POST.get('description', '')
            price = Decimal(request.POST.get('price', '0'))
            original_price = request.POST.get('original_price')
            original_price = Decimal(original_price) if original_price else None
            discount_label = request.POST.get('discount_label', '')
            is_active = request.POST.get('is_active') == 'on'
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE SERVICE 
                    SET ServiceName = %s, Category = %s, Description = %s, Price = %s, 
                        Original_Price = %s, Discount_Label = %s, is_active = %s
                    WHERE Service_ID = %s
                """, [service_name, category, description, price, original_price, discount_label, is_active, service_id])
                
            messages.success(request, 'Service updated successfully!')
            return redirect('admin_services')
        except Exception as e:
            messages.error(request, f'Error updating service: {str(e)}')
            return redirect('admin_services')
    return redirect('admin_services')


@admin_required
@csrf_protect
def admin_delete_service_view(request):
    """Delete service"""
    if request.method == 'POST':
        try:
            service_id = request.POST.get('service_id')
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM SERVICE WHERE Service_ID = %s", [service_id])
            messages.success(request, 'Service deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting service: {str(e)}')
    return redirect('admin_services')


# ============================================
# USER MANAGEMENT VIEWS
# ============================================

@admin_required
@csrf_protect
def admin_add_user_view(request):
    """Add new user (customer, employee, or admin)"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            
            with connection.cursor() as cursor:
                if user_type == 'customer':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    mobile = request.POST.get('mobile')
                    password = request.POST.get('password')
                    address = request.POST.get('address', '')
                    
                    cursor.execute("""
                        INSERT INTO CUSTOMER (First_Name, Last_Name, Mobile_No, Password, Address)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [first_name, last_name, mobile, password, address])
                    
                elif user_type == 'employee':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    phone = request.POST.get('phone')
                    address = request.POST.get('address', '')
                    skills = request.POST.get('skills', '')
                    rating = Decimal(request.POST.get('rating', '0'))
                    availability = request.POST.get('availability', 'available')
                    
                    cursor.execute("""
                        INSERT INTO EMPLOYEE (First_Name, Last_Name, Phone, Address, Skills, Rating, Availability)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [first_name, last_name, phone, address, skills, rating, availability])
                    
                elif user_type == 'admin':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    mobile = request.POST.get('mobile')
                    role = request.POST.get('role')
                    password = request.POST.get('password')
                    
                    cursor.execute("""
                        INSERT INTO ADMIN (First_Name, Last_Name, Mobile_No, Role, Password)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [first_name, last_name, mobile, role, password])
            
            messages.success(request, f'{user_type.capitalize()} added successfully!')
            tab_map = {'customer': 'customers', 'employee': 'employees', 'admin': 'admins'}
            return redirect(f"{reverse('admin_users')}?tab={tab_map.get(user_type, 'customers')}")
        except Exception as e:
            messages.error(request, f'Error adding {user_type}: {str(e)}')
            return redirect('admin_users')
    return redirect('admin_users')


@admin_required
def admin_get_user_view(request, user_type, user_id):
    """Get user details for editing"""
    try:
        with connection.cursor() as cursor:
            if user_type == 'customer':
                cursor.execute("""
                    SELECT Customer_ID, First_Name, Last_Name, Mobile_No, Address
                    FROM CUSTOMER WHERE Customer_ID = %s
                """, [user_id])
                row = cursor.fetchone()
                if row:
                    return JsonResponse({
                        'id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'mobile': row[3],
                        'address': row[4] or '',
                    })
                    
            elif user_type == 'employee':
                cursor.execute("""
                    SELECT Employee_ID, First_Name, Last_Name, Phone, Address, Skills, Rating, Availability
                    FROM EMPLOYEE WHERE Employee_ID = %s
                """, [user_id])
                row = cursor.fetchone()
                if row:
                    return JsonResponse({
                        'id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'phone': row[3],
                        'address': row[4] or '',
                        'skills': row[5] or '',
                        'rating': float(row[6]) if row[6] else 0.0,
                        'availability': row[7] or 'available',
                    })
                    
            elif user_type == 'admin':
                cursor.execute("""
                    SELECT Admin_ID, First_Name, Last_Name, Mobile_No, Role
                    FROM ADMIN WHERE Admin_ID = %s
                """, [user_id])
                row = cursor.fetchone()
                if row:
                    return JsonResponse({
                        'id': row[0],
                        'first_name': row[1],
                        'last_name': row[2],
                        'mobile': row[3],
                        'role': row[4],
                    })
    except Exception:
        pass
    return JsonResponse({'error': 'User not found'}, status=404)


@admin_required
@csrf_protect
def admin_edit_user_view(request):
    """Edit existing user"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')
            
            with connection.cursor() as cursor:
                if user_type == 'customer':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    mobile = request.POST.get('mobile')
                    password = request.POST.get('password')
                    address = request.POST.get('address', '')
                    
                    if password:
                        cursor.execute("""
                            UPDATE CUSTOMER 
                            SET First_Name = %s, Last_Name = %s, Mobile_No = %s, Password = %s, Address = %s, updated_at = NOW()
                            WHERE Customer_ID = %s
                        """, [first_name, last_name, mobile, password, address, user_id])
                    else:
                        cursor.execute("""
                            UPDATE CUSTOMER 
                            SET First_Name = %s, Last_Name = %s, Mobile_No = %s, Address = %s, updated_at = NOW()
                            WHERE Customer_ID = %s
                        """, [first_name, last_name, mobile, address, user_id])
                    
                elif user_type == 'employee':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    phone = request.POST.get('phone')
                    address = request.POST.get('address', '')
                    skills = request.POST.get('skills', '')
                    rating = Decimal(request.POST.get('rating', '0'))
                    availability = request.POST.get('availability', 'available')
                    
                    cursor.execute("""
                        UPDATE EMPLOYEE 
                        SET First_Name = %s, Last_Name = %s, Phone = %s, Address = %s, 
                            Skills = %s, Rating = %s, Availability = %s, updated_at = NOW()
                        WHERE Employee_ID = %s
                    """, [first_name, last_name, phone, address, skills, rating, availability, user_id])
                    
                elif user_type == 'admin':
                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    mobile = request.POST.get('mobile')
                    role = request.POST.get('role')
                    password = request.POST.get('password')
                    
                    if password:
                        cursor.execute("""
                            UPDATE ADMIN 
                            SET First_Name = %s, Last_Name = %s, Mobile_No = %s, Role = %s, Password = %s, updated_at = NOW()
                            WHERE Admin_ID = %s
                        """, [first_name, last_name, mobile, role, password, user_id])
                    else:
                        cursor.execute("""
                            UPDATE ADMIN 
                            SET First_Name = %s, Last_Name = %s, Mobile_No = %s, Role = %s, updated_at = NOW()
                            WHERE Admin_ID = %s
                        """, [first_name, last_name, mobile, role, user_id])
            
            messages.success(request, f'{user_type.capitalize()} updated successfully!')
            tab_map = {'customer': 'customers', 'employee': 'employees', 'admin': 'admins'}
            return redirect(f"{reverse('admin_users')}?tab={tab_map.get(user_type, 'customers')}")
        except Exception as e:
            messages.error(request, f'Error updating {user_type}: {str(e)}')
            return redirect('admin_users')
    return redirect('admin_users')


@admin_required
@csrf_protect
def admin_delete_user_view(request):
    """Delete user"""
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            user_id = request.POST.get('user_id')
            
            with connection.cursor() as cursor:
                if user_type == 'customer':
                    cursor.execute("DELETE FROM CUSTOMER WHERE Customer_ID = %s", [user_id])
                elif user_type == 'employee':
                    cursor.execute("DELETE FROM EMPLOYEE WHERE Employee_ID = %s", [user_id])
                elif user_type == 'admin':
                    cursor.execute("DELETE FROM ADMIN WHERE Admin_ID = %s", [user_id])
            
            messages.success(request, f'{user_type.capitalize()} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting {user_type}: {str(e)}')
    return redirect('admin_users')


@customer_required
def delete_address_view(request):
    """Delete saved address - plain text format (single address)"""
    from django.http import JsonResponse
    if request.method == 'POST':
        # Since we're using plain text, just clear the address
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE CUSTOMER
                        SET Address = NULL, updated_at = NOW()
                        WHERE Customer_ID = %s
                    """, [request.customer.Customer_ID])
                    
                    # Update customer object in session
                    request.customer.Address = None
            
            return JsonResponse({'success': True, 'message': 'Address deleted successfully'})
        except OperationalError as exc:
            return JsonResponse({'success': False, 'error': 'Unable to delete address. Please try again.'})


def serve_service_image(request, filename):
    """Serve service images from Assets/service images folder"""
    import os
    from django.conf import settings
    from urllib.parse import unquote
    from django.http import Http404
    
    # Decode the filename
    decoded_filename = unquote(filename)
    
    # Build the file path
    image_path = os.path.join(settings.BASE_DIR, 'Assets', 'service images', decoded_filename)
    
    # Security check: ensure the file is within the Assets directory
    if not os.path.abspath(image_path).startswith(os.path.abspath(os.path.join(settings.BASE_DIR, 'Assets'))):
        raise Http404("Invalid image path")
    
    # Check if file exists
    if not os.path.exists(image_path):
        raise Http404("Image not found")
    
    # Determine content type based on file extension
    content_type = 'image/jpeg'
    if decoded_filename.lower().endswith('.webp'):
        content_type = 'image/webp'
    elif decoded_filename.lower().endswith('.png'):
        content_type = 'image/png'
    elif decoded_filename.lower().endswith('.gif'):
        content_type = 'image/gif'
    
    # Read and return the image
    with open(image_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        return response
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

