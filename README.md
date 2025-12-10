# GLAMORA - Django Web Application

A modern Django web application for GLAMORA beauty salon, featuring appointment booking, service management, employee assignment, and receipt generation.

## Features

- **User Authentication**: Customer login, signup, and profile management
- **Service Management**: Browse and book beauty services
- **Appointment Booking**: Schedule appointments with date and time selection
- **Employee Assignment**: Automatic employee assignment for appointments
- **Payment Processing**: Secure payment handling with multiple payment methods
- **Receipt Generation**: PDF receipt generation for completed bookings
- **Admin Dashboard**: Comprehensive admin panel for managing services, appointments, sales, and employees
- **Modern UI**: Beautiful, responsive design with service images
- **Address Management**: Save and manage multiple addresses
- **Booking Management**: Edit and delete appointments (with 24-hour restriction)

## Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/GLAMORA.git
cd GLAMORA
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

- **On Windows:**
  ```bash
  venv\Scripts\activate
  ```

- **On macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Database Setup

#### Install MySQL

If you don't have MySQL installed:
- Download from: https://dev.mysql.com/downloads/mysql/
- Or use XAMPP/WAMP which includes MySQL

#### Create MySQL Database

1. **Start MySQL server**

2. **Create the database:**
   ```sql
   CREATE DATABASE glamora_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Run the database setup script:**
   - Open MySQL Workbench or command line
   - Execute all queries from `database_queries.sql`
   - This will create all necessary tables and sample data

#### Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   copy env.example .env
   ```
   (On Linux/Mac: `cp env.example .env`)

2. **Edit `.env` file** and add your database credentials:
   ```env
   DB_NAME=glamora_db
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

   **Note:** Replace `your_mysql_username` and `your_mysql_password` with your actual MySQL credentials.

### 6. Run Migrations (Optional)

```bash
python manage.py migrate
```

**Note:** This project uses raw SQL queries, so migrations are optional. The database structure is created via `database_queries.sql`.

### 7. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

## Running the Application

1. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

2. **Access the application:**
   - Open your browser and navigate to: `http://127.0.0.1:8000/`
   - Login page will be displayed by default

## Project Structure

```
GLAMORA/
├── Assets/                    # Static assets folder
│   ├── service images/        # Service images
│   ├── LOGO-1.jpg
│   └── Favicon.jpg
├── authentication/            # Main application
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── auth_helpers.py
├── glamora/                   # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                    # Static files (CSS, images)
│   ├── css/
│   └── images/
├── templates/                 # HTML templates
│   ├── base.html
│   └── authentication/
│       ├── login.html
│       ├── signup.html
│       ├── home.html
│       ├── services.html
│       ├── booking.html
│       ├── my_bookings.html
│       └── ...
├── database_queries.sql       # Database schema and sample data
├── requirements.txt          # Python dependencies
├── env.example               # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Main Pages

- **Login Page** (`/` or `/login/`): Customer login
- **Signup Page** (`/signup/`): New customer registration
- **Home Page** (`/home/`): Browse popular services
- **Services Page** (`/services/`): View all available services
- **Booking Page** (`/booking/`): Book an appointment
- **My Bookings** (`/my-bookings/`): View and manage appointments
- **My Receipts** (`/my-receipts/`): View booking receipts
- **Profile** (`/profile/`): Manage customer profile and settings
- **Admin Dashboard** (`/admin/`): Admin panel (requires admin login)

## Key Features Explained

### Appointment Booking
- Select service, date, and time slot
- Automatic employee assignment
- 24-hour edit restriction for appointments
- Payment processing with multiple methods

### Receipt Generation
- PDF receipt generation after booking confirmation
- View receipts in browser PDF viewer
- Download receipts for records

### Service Images
- Service-specific images displayed throughout the application
- Images stored in `Assets/service images/` folder

### Employee Management
- Employees automatically assigned to appointments
- Employee details displayed in booking cards
- Admin can manage employees through admin panel

## Database Schema

The application uses the following main tables:
- `CUSTOMER`: Customer information
- `SERVICE`: Available services
- `APPOINTMENT`: Booking appointments
- `EMPLOYEE`: Employee information
- `PAYMENT`: Payment records
- `SALES`: Sales transactions
- `RECEIPTS`: Receipt records
- `ADMIN`: Admin users

See `database_queries.sql` for complete schema.

## Configuration

### Environment Variables

The application uses `python-decouple` for configuration. Create a `.env` file based on `env.example`:

```env
DB_NAME=glamora_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### Static Files

Static files are served from:
- `static/` directory (CSS, JavaScript, images)
- `Assets/` directory (service images, logos)

## Development

### Making Changes

1. **Templates**: Modify files in `templates/authentication/`
2. **Styles**: Update `static/css/style.css`
3. **Views**: Add/modify views in `authentication/views.py`
4. **URLs**: Update routes in `authentication/urls.py`
5. **Database**: Modify queries in `database_queries.sql` or views

### Testing

- Test booking flow: Signup → Login → Book Service → Complete Payment
- Test admin features: Login as admin → Manage services/appointments
- Test receipt generation: Complete booking → View receipt

## Troubleshooting

### Database Connection Issues

- Ensure MySQL server is running
- Verify database credentials in `.env` file
- Check if database exists: `SHOW DATABASES;`
- Verify user has proper permissions

### Static Files Not Loading

- Run `python manage.py collectstatic` (if using production)
- Check `STATICFILES_DIRS` in `settings.py`
- Verify file paths in templates

### Service Images Not Displaying

- Ensure images are in `Assets/service images/` folder
- Check image filenames match service names in mapping
- Verify image serving URL in `authentication/urls.py`

## Security Notes

- **Never commit `.env` file** - It contains sensitive credentials
- Change `SECRET_KEY` in `settings.py` for production
- Set `DEBUG = False` in production
- Use environment variables for all sensitive data
- Keep database credentials secure

## Technologies Used

- **Backend**: Django 4.2.7
- **Database**: MySQL
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow
- **Configuration**: python-decouple

## License

This project is created for GLAMORA beauty salon application.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For issues or questions, please open an issue on GitHub.

---

**Note**: This application requires MySQL database. Make sure MySQL is installed and running before starting the Django server.
