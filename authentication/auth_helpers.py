"""
Custom authentication helpers for Customer and Admin authentication
"""
from django.shortcuts import redirect
from functools import wraps
from .models import Customer


def get_customer_from_session(request):
    """Get customer from session"""
    customer_id = request.session.get('customer_id')
    if customer_id:
        try:
            from django.db import connection
            db_executor = connection.cursor()
            db_executor.execute("SELECT Customer_ID, First_Name, Last_Name, Mobile_No, Password, Address FROM CUSTOMER WHERE Customer_ID = %s", [customer_id])
            row = db_executor.fetchone()
            
            if row:
                customer = Customer()
                customer.Customer_ID = row[0]
                customer.First_Name = row[1]
                customer.Last_Name = row[2]
                customer.Mobile_No = row[3]
                customer.Password = row[4]
                customer.Address = row[5] if len(row) > 5 else None
                return customer
        except Exception as e:
            print(f"Error getting customer from session: {e}")
            return None
    return None


def customer_login(request, customer):
    """Login customer by storing in session"""
    request.session['customer_id'] = customer.Customer_ID
    request.session['customer_mobile'] = customer.Mobile_No
    request.session['customer_name'] = f"{customer.First_Name} {customer.Last_Name}"


def customer_logout(request):
    """Logout customer by clearing session"""
    request.session.flush()


def customer_required(view_func):
    """Decorator to require customer login"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        customer = get_customer_from_session(request)
        if not customer:
            from django.contrib import messages
            messages.error(request, 'Please login to access this page.')
            from django.urls import reverse
            return redirect(reverse('login'))
        request.customer = customer
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Admin authentication helpers
def get_admin_from_session(request):
    """Get admin from session"""
    admin_id = request.session.get('admin_id')
    if admin_id:
        try:
            from django.db import connection
            db_executor = connection.cursor()
            db_executor.execute("SELECT Admin_ID, First_Name, Last_Name, Mobile_No, Role, Password FROM ADMIN WHERE Admin_ID = %s", [admin_id])
            row = db_executor.fetchone()
            
            if row:
                admin = type('Admin', (), {})()
                admin.Admin_ID = row[0]
                admin.First_Name = row[1]
                admin.Last_Name = row[2]
                admin.Mobile_No = row[3]
                admin.Role = row[4]
                admin.Password = row[5]
                return admin
        except Exception:
            return None
    return None


def admin_login(request, admin):
    """Login admin by storing in session"""
    request.session['admin_id'] = admin.Admin_ID
    request.session['admin_name'] = f"{admin.First_Name} {admin.Last_Name}"
    request.session['admin_role'] = admin.Role


def admin_logout(request):
    """Logout admin by clearing session"""
    request.session.flush()


def admin_required(view_func):
    """Decorator to require admin login"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        admin = get_admin_from_session(request)
        if not admin:
            from django.contrib import messages
            messages.error(request, 'Please login as admin to access this page.')
            from django.urls import reverse
            return redirect(reverse('login'))
        request.admin = admin
        return view_func(request, *args, **kwargs)
    return _wrapped_view

