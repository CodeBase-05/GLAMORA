-- =====================================================
-- Glamora Application - Database Schema Creation
-- =====================================================
-- This file contains SQL queries to create all tables
-- Based on ERD diagram: CUSTOMER, APPOINTMENT, EMPLOYEE, ADMIN, PAYMENT, SALES
-- Run these queries in MySQL Workbench
-- =====================================================

-- Use the database: Fall2025BIS698tueG5s
USE Fall2025BIS698tueG5s;

-- =====================================================
-- DELETE ALL EXISTING TABLES (Run this first to clean up)
-- =====================================================
-- WARNING: This will delete all data in these tables!
-- Run these queries if you need to recreate the tables
-- Note: Disabling foreign key checks to handle circular dependencies

SET FOREIGN_KEY_CHECKS = 0;

-- Legacy Django auth tables (created by default migrations)
DROP TABLE IF EXISTS auth_user_user_permissions;
DROP TABLE IF EXISTS auth_user_groups;
DROP TABLE IF EXISTS auth_group_permissions;
DROP TABLE IF EXISTS auth_permission;
DROP TABLE IF EXISTS auth_group;
DROP TABLE IF EXISTS auth_user;
DROP TABLE IF EXISTS django_admin_log;
DROP TABLE IF EXISTS django_session;
DROP TABLE IF EXISTS django_content_type;
DROP TABLE IF EXISTS django_migrations;

-- Legacy authentication app tables that referenced Django User
DROP TABLE IF EXISTS authentication_userprofile;
DROP TABLE IF EXISTS authentication_savedaddress;
DROP TABLE IF EXISTS authentication_savedcard;
DROP TABLE IF EXISTS authentication_booking;
DROP TABLE IF EXISTS authentication_customer;

-- Current MySQL-first tables
DROP TABLE IF EXISTS RECEIPTS;
DROP TABLE IF EXISTS APPOINTMENT;
DROP TABLE IF EXISTS SALES;
DROP TABLE IF EXISTS PAYMENT;
DROP TABLE IF EXISTS SERVICE;
DROP TABLE IF EXISTS ADMIN;
DROP TABLE IF EXISTS EMPLOYEE;
DROP TABLE IF EXISTS CUSTOMER;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- 1. CREATE CUSTOMER TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS CUSTOMER (
    Customer_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
    Last_Name VARCHAR(255) NOT NULL,
    Mobile_No VARCHAR(50) NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Address TEXT COMMENT 'Plain text address (not JSON)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mobile_no (Mobile_No)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. CREATE EMPLOYEE TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS EMPLOYEE (
    Employee_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
    Last_Name VARCHAR(255) NOT NULL,
    Phone VARCHAR(50) NOT NULL,
    Address TEXT,
    Skills TEXT,
    Rating DECIMAL(3,2) DEFAULT 0.00 CHECK (Rating >= 0 AND Rating <= 5),
    Availability ENUM('available', 'busy', 'unavailable') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_availability (Availability)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. CREATE ADMIN TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS ADMIN (
    Admin_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
    Last_Name VARCHAR(255) NOT NULL,
    Mobile_No VARCHAR(50) NOT NULL,
    Role VARCHAR(100) NOT NULL,
    Password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_mobile_no (Mobile_No)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 4. CREATE SERVICE TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS SERVICE (
    Service_ID INT AUTO_INCREMENT PRIMARY KEY,
    ServiceName VARCHAR(255) NOT NULL UNIQUE,
    Category ENUM('Deals', 'Hair', 'Waxing', 'Threading', 'Facial', 'Nails') NOT NULL DEFAULT 'Deals',
    Description TEXT,
    Price DECIMAL(10,2) NOT NULL CHECK (Price >= 0),
    Original_Price DECIMAL(10,2) DEFAULT NULL,
    Discount_Label VARCHAR(50) DEFAULT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service_name (ServiceName),
    INDEX idx_service_category (Category),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 5. CREATE PAYMENT TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS PAYMENT (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Appointment_ID INT,
    Amount DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Method ENUM('credit_card', 'debit_card') NOT NULL,
    Date DATE NOT NULL,
    Status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_appointment_id (Appointment_ID),
    INDEX idx_date (Date),
    INDEX idx_status (Status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 6. CREATE SALES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS SALES (
    Sales_ID INT AUTO_INCREMENT PRIMARY KEY,
    Payment_ID INT,
    Employee_ID INT,
    Admin_ID INT,
    Service_ID INT,
    ServiceName VARCHAR(255) NOT NULL,
    Date DATE NOT NULL,
    Receipt VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_payment_id (Payment_ID),
    INDEX idx_employee_id (Employee_ID),
    INDEX idx_admin_id (Admin_ID),
    INDEX idx_service_id (Service_ID),
    INDEX idx_date (Date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 7. CREATE APPOINTMENT TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS APPOINTMENT (
    Appointment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Employee_ID INT NOT NULL,
    Payment_ID INT,
    Admin_ID INT,
    Sales_ID INT,
    Date DATE NOT NULL,
    Time TIME NOT NULL,
    Status ENUM('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled') DEFAULT 'scheduled',
    Receipt VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (Customer_ID),
    INDEX idx_employee_id (Employee_ID),
    INDEX idx_payment_id (Payment_ID),
    INDEX idx_admin_id (Admin_ID),
    INDEX idx_sales_id (Sales_ID),
    INDEX idx_date (Date),
    INDEX idx_status (Status),
    -- Foreign Key Constraints
    CONSTRAINT fk_appointment_customer FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_employee FOREIGN KEY (Employee_ID) REFERENCES EMPLOYEE(Employee_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_payment FOREIGN KEY (Payment_ID) REFERENCES PAYMENT(Payment_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_admin FOREIGN KEY (Admin_ID) REFERENCES ADMIN(Admin_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_appointment_sales FOREIGN KEY (Sales_ID) REFERENCES SALES(Sales_ID) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 8. CREATE SAVED_CARDS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS SAVED_CARDS (
    Card_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Card_Number VARCHAR(16) NOT NULL COMMENT 'Complete 16-digit card number',
    Name_On_Card VARCHAR(255) NOT NULL,
    Expiry_Date VARCHAR(7) NOT NULL COMMENT 'Format: MM/YYYY',
    Card_Type ENUM('Credit Card', 'Debit Card') NOT NULL COMMENT 'Card type: Credit Card or Debit Card',
    Full_Card_Number VARCHAR(255) COMMENT 'Encrypted full card number (backup)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (Customer_ID),
    -- Foreign Key Constraint
    CONSTRAINT fk_saved_cards_customer FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 9. CREATE RECEIPTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS RECEIPTS (
    Receipt_ID INT AUTO_INCREMENT PRIMARY KEY,
    Receipt_Number VARCHAR(255) NOT NULL UNIQUE,
    Appointment_ID INT,
    Payment_ID INT,
    Sales_ID INT,
    Customer_ID INT NOT NULL,
    Amount DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Receipt_Date DATE NOT NULL,
    Receipt_File VARCHAR(500) COMMENT 'Path or URL to receipt file',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_receipt_number (Receipt_Number),
    INDEX idx_appointment_id (Appointment_ID),
    INDEX idx_payment_id (Payment_ID),
    INDEX idx_sales_id (Sales_ID),
    INDEX idx_customer_id (Customer_ID),
    INDEX idx_receipt_date (Receipt_Date),
    -- Foreign Key Constraints
    CONSTRAINT fk_receipts_appointment FOREIGN KEY (Appointment_ID) REFERENCES APPOINTMENT(Appointment_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_receipts_payment FOREIGN KEY (Payment_ID) REFERENCES PAYMENT(Payment_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_receipts_sales FOREIGN KEY (Sales_ID) REFERENCES SALES(Sales_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_receipts_customer FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 10. ADD FOREIGN KEY CONSTRAINTS FOR PAYMENT TABLE
-- =====================================================
-- Note: Payment references Appointment, but Appointment also references Payment
-- So we add this constraint after Appointment table is created
ALTER TABLE PAYMENT 
ADD CONSTRAINT fk_payment_appointment FOREIGN KEY (Appointment_ID) 
REFERENCES APPOINTMENT(Appointment_ID) ON DELETE SET NULL ON UPDATE CASCADE;

-- =====================================================
-- 11. ADD FOREIGN KEY CONSTRAINTS FOR SALES TABLE
-- =====================================================
ALTER TABLE SALES 
ADD CONSTRAINT fk_sales_payment FOREIGN KEY (Payment_ID) 
REFERENCES PAYMENT(Payment_ID) ON DELETE SET NULL ON UPDATE CASCADE,
ADD CONSTRAINT fk_sales_employee FOREIGN KEY (Employee_ID) 
REFERENCES EMPLOYEE(Employee_ID) ON DELETE CASCADE ON UPDATE CASCADE,
ADD CONSTRAINT fk_sales_admin FOREIGN KEY (Admin_ID) 
REFERENCES ADMIN(Admin_ID) ON DELETE SET NULL ON UPDATE CASCADE,
ADD CONSTRAINT fk_sales_service FOREIGN KEY (Service_ID) 
REFERENCES SERVICE(Service_ID) ON DELETE SET NULL ON UPDATE CASCADE;

-- =====================================================
-- 12. REMOVE SAVED_CARD COLUMN FROM CUSTOMER TABLE (if exists)
-- =====================================================
-- Run this to remove the Saved_Card column from CUSTOMER table
ALTER TABLE CUSTOMER DROP COLUMN IF EXISTS Saved_Card;

-- =====================================================
-- 12.1. UPDATE SAVED_CARDS TABLE - Change Card_Number to store full 16-digit number
-- =====================================================
-- Run this to update the Card_Number column to store full card number (16 digits)
ALTER TABLE SAVED_CARDS MODIFY COLUMN Card_Number VARCHAR(16) NOT NULL COMMENT 'Complete 16-digit card number';

-- =====================================================
-- 12.2. UPDATE SAVED_CARDS TABLE - Remove Method column and update Card_Type to ENUM
-- =====================================================
-- Run this to remove the Method column and update Card_Type to ENUM
ALTER TABLE SAVED_CARDS DROP COLUMN IF EXISTS Method;
ALTER TABLE SAVED_CARDS MODIFY COLUMN Card_Type ENUM('Credit Card', 'Debit Card') NOT NULL COMMENT 'Card type: Credit Card or Debit Card';

-- =====================================================
-- 12.3. UPDATE ADMIN TABLE - Add Mobile_No column for login
-- =====================================================
-- Run this to add Mobile_No column to ADMIN table
ALTER TABLE ADMIN ADD COLUMN IF NOT EXISTS Mobile_No VARCHAR(50) NOT NULL DEFAULT '' AFTER Last_Name;
ALTER TABLE ADMIN ADD INDEX IF NOT EXISTS idx_mobile_no (Mobile_No);

-- =====================================================
-- 13. VIEW ALL CREATED TABLES
-- =====================================================
SHOW TABLES;

-- =====================================================
-- 14. VIEW TABLE STRUCTURES
-- =====================================================
DESCRIBE CUSTOMER;
DESCRIBE EMPLOYEE;
DESCRIBE ADMIN;
DESCRIBE SERVICE;
DESCRIBE PAYMENT;
DESCRIBE SALES;
DESCRIBE APPOINTMENT;
DESCRIBE RECEIPTS;
DESCRIBE SAVED_CARDS;

-- =====================================================
-- 15. VERIFY DATABASE CONNECTION
-- =====================================================
SELECT 
    DATABASE() as current_database,
    USER() as current_user,
    NOW() as current_time;

-- =====================================================
-- 16. SAMPLE DATA (RUN AFTER TABLES ARE CREATED)
-- =====================================================
-- The following INSERT statements seed the database with realistic data
-- so the Django application has something to display immediately.
-- Run them only on a clean database (after DROP/CREATE above).

-- -----------------------------------------------------
-- 14.1 CUSTOMER SAMPLE DATA
-- -----------------------------------------------------
-- NOTE: Customer_ID = 1 already exists in the live database.
--       Only insert the additional seed customers below.
INSERT INTO CUSTOMER (Customer_ID, First_Name, Last_Name, Mobile_No, Password, Address)
VALUES
    (2, 'Ava', 'Mitchell', '13125551212', 'Beauty123', '742 Maple Ave, Lansing, MI'),
    (3, 'Liam', 'Patel', '13129994444', 'SpaDay!', '18 Pearl St, Grand Rapids, MI');

-- -----------------------------------------------------
-- 14.2 EMPLOYEE SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO EMPLOYEE (Employee_ID, First_Name, Last_Name, Phone, Address, Skills, Rating, Availability)
VALUES
    (1, 'Sophia', 'Reed', '13125550001', '901 Willow St, Detroit, MI', 'Color, Styling', 4.80, 'available'),
    (2, 'Maya', 'Singh', '13125550002', '45 Horizon Rd, Troy, MI', 'Spa, Facial', 4.65, 'available'),
    (3, 'Olivia', 'Chen', '13125550003', '12 Lakeview Dr, Novi, MI', 'Nails, Threading', 4.50, 'busy');

-- -----------------------------------------------------
-- 14.3 ADMIN SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO ADMIN (Admin_ID, First_Name, Last_Name, Mobile_No, Role, Password)
VALUES
    (1, 'Harper', 'James', '1234567890', 'Studio Manager', 'ManagerPass1'),
    (2, 'Noah', 'Bennett', '0987654321', 'Assistant Manager', 'ManagerPass2');

-- -----------------------------------------------------
-- 14.4 SERVICE SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO SERVICE (Service_ID, ServiceName, Category, Description, Price, Original_Price, Discount_Label, is_active)
VALUES
    (1, 'Hair Cut & Styling', 'Hair', 'Professional haircut with styling', 45.00, 56.25, '20% OFF', TRUE),
    (2, 'Full Body Waxing', 'Waxing', 'Complete body waxing service', 85.00, NULL, NULL, TRUE),
    (3, 'Facial Treatment', 'Facial', 'Deep cleansing facial with massage', 65.00, 76.47, '15% OFF', TRUE),
    (4, 'Threading', 'Threading', 'Eyebrow and facial threading', 25.00, NULL, NULL, TRUE),
    (5, 'Manicure & Pedicure', 'Nails', 'Complete nail care service', 55.00, NULL, NULL, TRUE),
    (6, 'Hair Coloring', 'Hair', 'Professional hair coloring service', 120.00, 133.33, '10% OFF', TRUE),
    (7, 'Hair Wash', 'Hair', 'Professional hair washing service', 20.00, NULL, NULL, TRUE),
    (8, 'Hair Colour', 'Hair', 'Vibrant colouring service', 100.00, NULL, NULL, TRUE),
    (9, 'Styling', 'Hair', 'Hair styling service', 35.00, NULL, NULL, TRUE),
    (10, 'Eyebrow Threading', 'Threading', 'Eyebrow threading service', 15.00, NULL, NULL, TRUE),
    (11, 'Facial Threading', 'Threading', 'Facial threading service', 20.00, NULL, NULL, TRUE),
    (12, 'Deep Cleansing Facial', 'Facial', 'Deep cleansing facial treatment', 70.00, NULL, NULL, TRUE),
    (13, 'Manicure', 'Nails', 'Professional manicure service', 30.00, NULL, NULL, TRUE),
    (14, 'Pedicure', 'Nails', 'Professional pedicure service', 35.00, NULL, NULL, TRUE),
    (15, 'Nail Art', 'Nails', 'Creative nail art design', 25.00, NULL, NULL, TRUE),
    (16, 'Hair & Facial Combo', 'Deals', 'Hair Cut & Styling + Facial Treatment combo', 95.00, 110.00, '15% OFF', TRUE),
    (17, 'Complete Beauty Package', 'Deals', 'Full day beauty and spa experience', 180.00, 220.00, '18% OFF', TRUE),
    (18, 'Hair & Nails Combo', 'Deals', 'Hair styling with manicure and pedicure', 75.00, 90.00, '17% OFF', TRUE),
    (19, 'Threading & Facial Combo', 'Deals', 'Eyebrow threading with mini facial', 70.00, 85.00, '18% OFF', TRUE),
    (20, 'Full Body Care Package', 'Deals', 'Waxing, facial and nail care package', 150.00, 180.00, '17% OFF', TRUE),
    (21, 'Hair Color & Styling Combo', 'Deals', 'Color refresh with signature styling', 130.00, 155.00, '16% OFF', TRUE);

-- -----------------------------------------------------
-- 14.5 APPOINTMENT SAMPLE DATA (Payment_ID/Sales_ID filled later)
-- -----------------------------------------------------
INSERT INTO APPOINTMENT (Appointment_ID, Customer_ID, Employee_ID, Admin_ID, Date, Time, Status, Receipt)
VALUES
    (1, 1, 1, 1, '2025-12-01', '10:00:00', 'confirmed', 'RCPT-1001'),
    (2, 2, 2, 2, '2025-12-02', '13:30:00', 'completed', 'RCPT-1002'),
    (3, 3, 3, 1, '2025-12-03', '15:00:00', 'scheduled', 'RCPT-1003');

-- -----------------------------------------------------
-- 14.6 PAYMENT SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO PAYMENT (Payment_ID, Appointment_ID, Amount, Method, Date, Status)
VALUES
    (1, 1, 120.00, 'credit_card', '2025-12-01', 'completed'),
    (2, 2, 155.00, 'debit_card',  '2025-12-02', 'completed'),
    (3, 3,  90.00, 'credit_card', '2025-12-03', 'pending');

-- Tie the payments back to the appointments now that IDs exist.
UPDATE APPOINTMENT SET Payment_ID = 1 WHERE Appointment_ID = 1;
UPDATE APPOINTMENT SET Payment_ID = 2 WHERE Appointment_ID = 2;
UPDATE APPOINTMENT SET Payment_ID = 3 WHERE Appointment_ID = 3;

-- -----------------------------------------------------
-- 14.7 SALES SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO SALES (Sales_ID, Payment_ID, Employee_ID, Admin_ID, Service_ID, ServiceName, Date, Receipt)
VALUES
    (1, 1, 1, 1, 1, 'Signature Haircut', '2025-12-01', 'SALE-5001'),
    (2, 2, 2, 2, 2, 'Luxury Facial',    '2025-12-02', 'SALE-5002');

-- Update appointments with sales that were generated.
UPDATE APPOINTMENT SET Sales_ID = 1 WHERE Appointment_ID = 1;
UPDATE APPOINTMENT SET Sales_ID = 2 WHERE Appointment_ID = 2;

-- -----------------------------------------------------
-- 14.8 RECEIPTS SAMPLE DATA
-- -----------------------------------------------------
INSERT INTO RECEIPTS (Receipt_ID, Receipt_Number, Appointment_ID, Payment_ID, Sales_ID, Customer_ID, Amount, Receipt_Date, Receipt_File)
VALUES
    (1, 'RCPT-1001', 1, 1, 1, 1, 120.00, '2025-12-01', 'receipts/RCPT-1001.pdf'),
    (2, 'RCPT-1002', 2, 2, 2, 2, 155.00, '2025-12-02', 'receipts/RCPT-1002.pdf'),
    (3, 'RCPT-1003', 3, 3, NULL, 3,  90.00, '2025-12-03', 'receipts/RCPT-1003.pdf');

-- -----------------------------------------------------
-- 14.9 SAMPLE DATA VERIFICATION
-- -----------------------------------------------------
SELECT 'CUSTOMER' AS table_name, COUNT(*) AS total_rows FROM CUSTOMER
UNION ALL
SELECT 'EMPLOYEE', COUNT(*) FROM EMPLOYEE
UNION ALL
SELECT 'ADMIN', COUNT(*) FROM ADMIN
UNION ALL
SELECT 'SERVICE', COUNT(*) FROM SERVICE
UNION ALL
SELECT 'APPOINTMENT', COUNT(*) FROM APPOINTMENT
UNION ALL
SELECT 'PAYMENT', COUNT(*) FROM PAYMENT
UNION ALL
SELECT 'SALES', COUNT(*) FROM SALES
UNION ALL
SELECT 'RECEIPTS', COUNT(*) FROM RECEIPTS;

-- =====================================================
-- 17. DELETE ALL BOOKINGS FROM APPOINTMENT TABLE
-- =====================================================
-- WARNING: This will delete all appointments/bookings from the APPOINTMENT table
-- Use this query to remove all bookings
-- Note: Uses WHERE clause with key column to work with MySQL safe update mode
DELETE FROM APPOINTMENT WHERE Appointment_ID > 0;

-- =====================================================
-- 18. DELETE ALL DATA FROM RECEIPTS TABLE
-- =====================================================
-- WARNING: This will delete all receipts from the RECEIPTS table
-- Use this query to remove all receipts
-- Note: Uses WHERE clause with key column to work with MySQL safe update mode
DELETE FROM RECEIPTS WHERE Receipt_ID > 0;

-- =====================================================
-- 19. DELETE ALL DATA FROM SALES TABLE
-- =====================================================
-- WARNING: This will delete all sales records from the SALES table
-- Use this query to remove all sales
-- Note: Uses WHERE clause with key column to work with MySQL safe update mode
DELETE FROM SALES WHERE Sales_ID > 0;
