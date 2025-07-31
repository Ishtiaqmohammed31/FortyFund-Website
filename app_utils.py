from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import os
from werkzeug.utils import secure_filename
from datetime import date # Import date for handling publish_date
from functools import wraps # Import wraps for decorator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import time
from dotenv import load_dotenv 
load_dotenv()

# --- Admin Credentials ---
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# for establishing db connection
def get_db_connection():
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,          # Replace with your MySQL username
        password=DB_PASSWORD, # Replace with your MySQL password
        database=DB_NAME # Updated to your new database name
    )
    return conn

# authentication decorator 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



# returning connection

def return_content():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all content from all tables according to new schema
    cursor.execute("SELECT * FROM navtable WHERE nav_id = 1")
    nav_content = cursor.fetchone()

    cursor.execute("SELECT * FROM herotable WHERE hero_id = 1")
    hero_content = cursor.fetchone()

    cursor.execute("SELECT * FROM clientTrust WHERE clientTrust_id = 1")
    client_trust_content = cursor.fetchone()

    cursor.execute("SELECT * FROM innovationTable WHERE innovation_id = 1")
    innovation_content = cursor.fetchone()

    cursor.execute("SELECT * FROM clientExperience WHERE clientExp_id = 1")
    experience_content = cursor.fetchone()

    cursor.execute("SELECT * FROM statistics WHERE statistics_id = 1")
    stats_content = cursor.fetchone()

    cursor.execute("SELECT * FROM stat_card WHERE statCard_id = 1")
    stat_card_content = cursor.fetchone()

    cursor.execute("SELECT * FROM getToKnow WHERE knowId = 1")
    know_content = cursor.fetchone()

    cursor.execute("SELECT * FROM exploreTable WHERE explore_id = 1")
    explore_content = cursor.fetchone()

    cursor.execute("SELECT * FROM footer WHERE footer_id = 1")
    footer = cursor.fetchone()

    # Fetch latest blogs for the 'Explore' section (e.g., for index page)
    # Join with Images table to get thumbnail details
    cursor.execute("""
        SELECT
            b.blog_id,
            b.heading,
            b.subheading,
            b.author,
            b.publish_date,
            b.content,
            i.image_filename AS thumbnail_image_filename,
            i.alt_text AS thumbnail_image_alt_text
        FROM Blogs b
        LEFT JOIN Images i ON b.thumbnail_image_id = i.image_id
        ORDER BY b.publish_date DESC
        LIMIT 9 # Fetch a reasonable number of latest blogs
    """)
    latest_blogs = cursor.fetchall()

    # Fetch all FAQs and group by category
    cursor.execute("SELECT * FROM faqs ORDER BY category, faq_id")
    all_faqs = cursor.fetchall()
    faqs_by_category = {}
    for faq in all_faqs:
        category = faq['category']
        if category not in faqs_by_category:
            faqs_by_category[category] = []
        faqs_by_category[category].append(faq)

    # Fetch contact submissions
    cursor.execute("SELECT * FROM contact_submissions ORDER BY submission_date DESC")
    contact_submissions = cursor.fetchall()


    conn.close()

    # Combine all content into a single dictionary for easier access in Jinja
    content = {
        **(nav_content or {}),
        **(hero_content or {}),
        **(client_trust_content or {}),
        **(innovation_content or {}),
        **(experience_content or {}),
        **(stats_content or {}),
        **(stat_card_content or {}),
        **(know_content or {}),
        **(explore_content or {}),
        **(footer or {} ),
        'latest_blogs': latest_blogs, # Add latest blogs to the content
        'faqs_by_category': faqs_by_category, # Add grouped FAQs
        'contact_submissions': contact_submissions # Add contact submissions
    }

    return content


# send email

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")