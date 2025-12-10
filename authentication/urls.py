from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('signup/', views.signup_view, name='signup'),
    path('signup/success/', views.signup_success_view, name='signup_success'),
    path('home/', views.home_view, name='home'),
    path('services/', views.services_view, name='services'),
    path('search/', views.search_results_view, name='search'),
    path('booking/', views.booking_view, name='booking'),
    path('payment/', views.payment_view, name='payment'),
    path('address/', views.address_view, name='address'),
    path('booking-confirmation/<int:receipt_id>/', views.booking_confirmation_view, name='booking_confirmation'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('delete-booking/', views.delete_booking_view, name='delete_booking'),
    path('edit-booking/', views.edit_booking_view, name='edit_booking'),
    path('update-booking/', views.update_booking_view, name='update_booking'),
    path('my-receipts/', views.my_receipts_view, name='my_receipts'),
    path('view-receipt-pdf/<int:receipt_id>/', views.view_receipt_pdf, name='view_receipt_pdf'),
    path('delete-receipt/', views.delete_receipt_view, name='delete_receipt'),
    path('saved-addresses/', views.saved_addresses_view, name='saved_addresses'),
    path('delete-address/', views.delete_address_view, name='delete_address'),
    path('profile-settings/', views.profile_settings_view, name='profile_settings'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('profile/', views.profile_view, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    # Admin routes
    path('admin/home/', views.admin_home_view, name='admin_home'),
    path('admin/services/', views.admin_services_view, name='admin_services'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/appointments/', views.admin_appointments_view, name='admin_appointments'),
    path('admin/sales/', views.admin_sales_view, name='admin_sales'),
    # Service management
    path('admin/add-service/', views.admin_add_service_view, name='admin_add_service'),
    path('admin/edit-service/', views.admin_edit_service_view, name='admin_edit_service'),
    path('admin/delete-service/', views.admin_delete_service_view, name='admin_delete_service'),
    path('admin/get-service/<int:service_id>/', views.admin_get_service_view, name='admin_get_service'),
    # User management
    path('admin/add-user/', views.admin_add_user_view, name='admin_add_user'),
    path('admin/edit-user/', views.admin_edit_user_view, name='admin_edit_user'),
    path('admin/delete-user/', views.admin_delete_user_view, name='admin_delete_user'),
    path('admin/get-user/<str:user_type>/<int:user_id>/', views.admin_get_user_view, name='admin_get_user'),
    # Service images
    path('service-images/<path:filename>', views.serve_service_image, name='serve_service_image'),
]

