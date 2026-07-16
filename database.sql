-- MySQL Database Script for Student Course Management Portal
-- Database: `student_course_portal`

CREATE DATABASE IF NOT EXISTS `student_course_portal`;
USE `student_course_portal`;

-- 1. Students Table
CREATE TABLE IF NOT EXISTS `students` (
  `student_id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `mobile` VARCHAR(20) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `date_of_birth` DATE NOT NULL,
  `gender` VARCHAR(10) NOT NULL,
  `profile_picture` VARCHAR(255) DEFAULT 'default_profile.png',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Admin Table
CREATE TABLE IF NOT EXISTS `admin` (
  `admin_id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(100) UNIQUE NOT NULL,
  `password` VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Courses Table
CREATE TABLE IF NOT EXISTS `courses` (
  `course_id` INT AUTO_INCREMENT PRIMARY KEY,
  `course_name` VARCHAR(150) NOT NULL,
  `description` TEXT NOT NULL,
  `duration` VARCHAR(50) NOT NULL,
  `fee` DECIMAL(10, 2) NOT NULL,
  `instructor_name` VARCHAR(100) NOT NULL,
  `instructor_email` VARCHAR(100) NOT NULL,
  `course_image` VARCHAR(255) DEFAULT 'default_course.png',
  `status` VARCHAR(10) DEFAULT 'Active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Enrollments Table
CREATE TABLE IF NOT EXISTS `enrollments` (
  `enrollment_id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `course_id` INT NOT NULL,
  `payment_status` VARCHAR(20) DEFAULT 'Unpaid',
  `enrollment_status` VARCHAR(50) DEFAULT 'Pending Payment',
  `payment_reference` VARCHAR(100) DEFAULT NULL,
  `enrollment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Contact Messages Table
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `message_id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(150) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `admin_reply` TEXT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Announcements Table
CREATE TABLE IF NOT EXISTS `announcements` (
  `announcement_id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  `discount_percent` DOUBLE DEFAULT NULL,
  `is_offer` TINYINT(1) DEFAULT 0,
  `is_active` TINYINT(1) DEFAULT 1,
  `start_at` DATETIME DEFAULT NULL,
  `expires_at` DATETIME DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6a. Offer Courses (Many-to-Many join table)
CREATE TABLE IF NOT EXISTS `offer_courses` (
  `announcement_id` INT NOT NULL,
  `course_id` INT NOT NULL,
  PRIMARY KEY (`announcement_id`, `course_id`),
  FOREIGN KEY (`announcement_id`) REFERENCES `announcements` (`announcement_id`) ON DELETE CASCADE,
  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6b. Inquiries Table (support both registered students and public visitors)
CREATE TABLE IF NOT EXISTS `inquiries` (
  `inquiry_id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT DEFAULT NULL,
  `course_id` INT DEFAULT NULL,
  `name` VARCHAR(150) DEFAULT NULL,
  `email` VARCHAR(100) DEFAULT NULL,
  `mobile` VARCHAR(20) DEFAULT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `message` TEXT NOT NULL,
  `status` VARCHAR(20) DEFAULT 'Pending',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,
  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6c. Inquiry Replies Table
CREATE TABLE IF NOT EXISTS `inquiry_replies` (
  `reply_id` INT AUTO_INCREMENT PRIMARY KEY,
  `inquiry_id` INT NOT NULL,
  `sender_role` VARCHAR(10) NOT NULL,
  `message` TEXT NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`inquiry_id`) REFERENCES `inquiries` (`inquiry_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Notifications Table
CREATE TABLE IF NOT EXISTS `notifications` (
  `notification_id` INT AUTO_INCREMENT PRIMARY KEY,
  `student_id` INT NOT NULL,
  `title` VARCHAR(150) NOT NULL,
  `message` TEXT NOT NULL,
  `is_read` TINYINT(1) DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Seeding default data
-- Note: Default Admin Credentials are admin@portal.com / Admin@123
-- Password hash: scrypt:32768:8:1$kQfB4WpTNVY4s9wR$9d91bd13180c427848d7d91e... (we handle this python-side dynamically for portability, but seed tables if running raw scripts)
INSERT INTO `admin` (`name`, `email`, `password`) 
SELECT 'Portal Administrator', 'admin@portal.com', 'scrypt:32768:8:1$O0N8cpx9nS92fQ5a$ffc96a55e1dbba22119eb31c89feea3862cd5d082fa2c92b21734a6cf83d2890539b9bfcc60cc445ca1029c7cc91e6b36440c9462d7c50a4ecdbfbc5f22e8ec5'
WHERE NOT EXISTS (SELECT 1 FROM `admin` WHERE `email` = 'admin@portal.com');

-- Seeding some initial courses
INSERT INTO `courses` (`course_name`, `description`, `duration`, `fee`, `instructor_name`, `instructor_email`, `status`)
VALUES 
('Introduction to Python Programming', 'Learn the basics of Python, from syntax and control flows to object-oriented programming.', '6 Weeks', 149.99, 'Dr. Sarah Jenkins', 'sarah.j@portal.com', 'Active'),
('Full Stack Web Development', 'Master HTML, CSS, JavaScript, Bootstrap, Flask, and Database deployments.', '12 Weeks', 299.99, 'Prof. Alex Mercer', 'alex.m@portal.com', 'Active'),
('Data Science and Machine Learning', 'Dive deep into pandas, numpy, scikit-learn, and create your first classification models.', '10 Weeks', 249.99, 'Dr. Sarah Jenkins', 'sarah.j@portal.com', 'Active');
