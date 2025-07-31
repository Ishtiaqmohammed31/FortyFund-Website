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
from app_utils import get_db_connection, login_required, return_content, send_email
from dotenv import load_dotenv  

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for sensitive config
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# --- Admin Credentials ---
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# inside 'static/assets/uploads'.
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'assets', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Email Utility ---
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

def handle_upload(file, field_name):
    """
    Handles file uploads, saves them, and returns the static path.
    field_name can be used to create subdirectories if needed, or just for logging.
    """
    if file and file.filename:
        filename = secure_filename(file.filename)
        # Use app.config['UPLOAD_FOLDER'] which is already an absolute path
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Return path relative to static for URL usage
        return f"static/assets/uploads/{filename}"
    return None


@app.route('/')
def index():
    content = return_content()
    return render_template('index.html', **content)

@app.route('/blog/<int:blog_id>')
def blog(blog_id):
    """
    Route to display a sing-le blog post.
    Fetches blog details and its thumbnail image from the database.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

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
        WHERE b.blog_id = %s
    """, (blog_id,))
    blog_post = cursor.fetchone()
    conn.close()

    content = return_content()

    if blog_post:
        return render_template('blog.html',**content, **blog_post)
    else:
        flash('Blog post not found!', 'error')
        return redirect(url_for('index'))

# --- Login and Logout Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required # Protect this route
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Determine which form was submitted based on a hidden input or specific field names
            form_type = request.form.get('form_type')

            if form_type == 'add_faq':
                category = request.form['faqCategory']
                question = request.form['faqQuestion']
                answer = request.form['faqAnswer']
                cursor.execute("INSERT INTO faqs (category, question, answer) VALUES (%s, %s, %s)",
                               (category, question, answer))
                conn.commit()
                flash('FAQ added successfully!', 'success')
                return redirect(url_for('admin'))

            elif form_type == 'edit_faq':
                faq_id = request.form['faq_id']
                category = request.form['faqCategory']
                question = request.form['faqQuestion']
                answer = request.form['faqAnswer']
                cursor.execute("UPDATE faqs SET category = %s, question = %s, answer = %s WHERE faq_id = %s",
                               (category, question, answer, faq_id))
                conn.commit()
                flash('FAQ updated successfully!', 'success')
                return redirect(url_for('admin'))

            elif form_type == 'update_main_content': # New condition for main content form
                # Existing content update logic
                # Update Navbar Section (navtable)
                nav_logo_file = request.files.get('navLogo')
                nav_logo_path = handle_upload(nav_logo_file, 'navLogo') or request.form.get('currentNavLogo')
                cursor.execute("""
                    UPDATE navtable SET
                    navLogo = %s, navAnchor1 = %s, navAnchor2 = %s, navAnchor3 = %s,
                    dropdown1 = %s, dropdown2 = %s, navbtn = %s
                    WHERE nav_id = 1
                """, (
                    nav_logo_path, request.form['navAnchor1'], request.form['navAnchor2'],
                    request.form['navAnchor3'], request.form['dropdown1'], request.form['dropdown2'],
                    request.form['navbtn']
                ))

                # Update Hero Section (herotable)
                hero_img_file = request.files.get('heroImg')
                hero_img_path = handle_upload(hero_img_file, 'heroImg') or request.form.get('currentHeroImg')
                cursor.execute("""
                    UPDATE herotable SET
                    heroHeading = %s, heroDescription = %s, heroImg = %s
                    WHERE hero_id = 1
                """, (request.form['heroHeading'], request.form['heroDescription'], hero_img_path))

                # Update Client Trust Section (clientTrust)
                cursor.execute("""
                    UPDATE clientTrust SET
                    clientHeading = %s, clientDescription = %s
                    WHERE clientTrust_id = 1
                """, (request.form['clientHeading'], request.form['clientDescription']))
                for i in range(1, 10):
                    cl_img_file = request.files.get(f'clientImg{i}')
                    cl_img_path = handle_upload(cl_img_file, f'clientImg{i}') or request.form.get(f'currentClientImg{i}')
                    if cl_img_path:
                        cursor.execute(f"UPDATE clientTrust SET clientImg{i} = %s WHERE clientTrust_id = 1", (cl_img_path,))


                # Update Innovation Section (innovationTable)
                innovation_video_file = request.files.get('innovationVideo')
                innovation_video_path = handle_upload(innovation_video_file, 'innovationVideo') or request.form.get('currentInnovationVideo')
                cursor.execute("""
                    UPDATE innovationTable SET
                    innovationHeadTop = %s, innovationHeadmain = %s, innovationDescription = %s,
                    li1 = %s, li2 = %s, li3 = %s, li4 = %s, innovationVideo = %s
                    WHERE innovation_id = 1
                """, (
                    request.form['innovationHeadTop'], request.form['innovationHeadmain'], request.form['innovationDescription'],
                    request.form['li1'], request.form['li2'], request.form['li3'], request.form['li4'],
                    innovation_video_path
                ))

                # Update Client Experience Section (clientExperience)
                exp_video_file = request.files.get('clientExpVideo')
                exp_video_path = handle_upload(exp_video_file, 'clientExpVideo') or request.form.get('currentClientExpVideo')
                cursor.execute("""
                    UPDATE clientExperience SET
                    clientExpHead = %s, clientExpDescription = %s, clientExpVideo = %s
                    WHERE clientExp_id = 1
                """, (
                    request.form['clientExpHead'], request.form['clientExpDescription'], exp_video_path
                ))

                # Update Statistics Section (statistics)
                cursor.execute("""
                    UPDATE statistics SET
                    statHead = %s, statDescription = %s
                    WHERE statistics_id = 1
                """, (request.form['statHead'], request.form['statDescription']))

                # Update Stat Card Section (stat_card) - new table
                for i in range(1, 4):
                    card_logo_file = request.files.get(f'StatcardLogo{i}')
                    card_logo_path = handle_upload(card_logo_file, f'StatcardLogo{i}') or request.form.get(f'currentStatcardLogo{i}')
                    if card_logo_path:
                        cursor.execute(f"UPDATE stat_card SET StatcardLogo{i} = %s WHERE statCard_id = 1", (card_logo_path,))
                cursor.execute("""
                    UPDATE stat_card SET
                    StatcardHead1 = %s, StatcardPara1 = %s,
                    StatcardHead2 = %s, StatcardPara2 = %s,
                    StatcardHead3 = %s, StatcardPara3 = %s
                    WHERE statCard_id = 1
                """, (
                    request.form['StatcardHead1'], request.form['StatcardPara1'],
                    request.form['StatcardHead2'], request.form['StatcardPara2'],
                    request.form['StatcardHead3'], request.form['StatcardPara3']
                ))

                # Update Get to Know Section (getToKnow)
                know_video_file = request.files.get('knowVideo')
                know_video_path = handle_upload(know_video_file, 'knowVideo') or request.form.get('currentKnowVideo')
                cursor.execute("""
                    UPDATE getToKnow SET
                    knowHead = %s, knowVideo = %s
                    WHERE knowId = 1
                """, (request.form['knowHead'], know_video_path))

                # Update Explore Industries and Services Section (exploreTable)
                cursor.execute("""
                    UPDATE exploreTable SET
                    exploreHeading = %s
                    WHERE explore_id = 1
                """, (request.form['exploreHeading'],))


                # Update Footer Section (footer)
                social_img1_file = request.files.get('footer_social_icon1')
                social_img1_path = handle_upload(social_img1_file, 'footer_social_icon1') or request.form.get('current_footer_social_icon1')

                social_img2_file = request.files.get('footer_social_icon2')
                social_img2_path = handle_upload(social_img2_file, 'footer_social_icon2') or request.form.get('current_footer_social_icon2')

                social_img3_file = request.files.get('footer_social_icon3')
                social_img3_path = handle_upload(social_img3_file, 'footer_social_icon3') or request.form.get('current_footer_social_icon3')

                social_img4_file = request.files.get('footer_social_icon4')
                social_img4_path = handle_upload(social_img4_file, 'footer_social_icon4') or request.form.get('current_footer_social_icon4')

                cursor.execute("""
                    UPDATE footer SET
                    footer_logo = %s,
                    footer_social_icon1 = %s, footer_social_link1 = %s,
                    footer_social_icon2 = %s, footer_social_link2 = %s,
                    footer_social_icon3 = %s, footer_social_link3 = %s,
                    footer_social_icon4 = %s, footer_social_link4 = %s
                    WHERE footer_id = 1
                """, (
                    request.form['footer_logo'],
                    social_img1_path, request.form['footer_social_link1'],
                    social_img2_path, request.form['footer_social_link2'],
                    social_img3_path, request.form['footer_social_link3'],
                    social_img4_path, request.form['footer_social_link4']
                ))


                conn.commit()
                flash('Content updated successfully!', 'success')
                return redirect(url_for('admin'))
            else:
                flash('Unknown form submission type.', 'error')


        except Exception as e:
            conn.rollback()
            flash(f'An error occurred: {e}', 'error')
            print(f"Error: {e}") # For debugging

    # Fetch all content for the GET request (and initial form population)
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
    footer_content = cursor.fetchone()

    # Fetch all blogs for display in the admin panel
    cursor.execute("""
        SELECT
            b.blog_id,
            b.heading,
            b.author,
            b.publish_date,
            i.image_filename AS thumbnail_image_filename
        FROM Blogs b
        LEFT JOIN Images i ON b.thumbnail_image_id = i.image_id
        ORDER BY b.publish_date DESC
    """)
    all_blogs = cursor.fetchall()

    # Fetch all FAQs for display in the admin panel
    cursor.execute("SELECT * FROM faqs ORDER BY category, faq_id")
    all_faqs = cursor.fetchall()

    # Fetch contact submissions (assuming a table named contact_submissions)
    try:
        cursor.execute("SELECT * FROM contact_submissions ORDER BY submission_date DESC")
        contact_submissions = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching contact submissions: {err}")
        contact_submissions = [] # Initialize as empty list if table doesn't exist

    # Fetch all demo bookings for admin panel display
    try:
        cursor.execute("SELECT * FROM demo_bookings ORDER BY meeting_date DESC")
        all_demo_bookings = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching demo bookings: {err}")
        all_demo_bookings = [] # Initialize as empty list if table doesn't exist


    conn.close()

    # Combine all content into a single dictionary for the admin panel
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
        **(footer_content or {}),
        'all_blogs': all_blogs, # Add all blogs to the content for admin
        'all_faqs': all_faqs, # Add all FAQs for admin
        'contact_submissions': contact_submissions, # Add contact submissions
        'all_demo_bookings': all_demo_bookings # Add all demo bookings for admin
    }

    return render_template('admin.html', content=content)


# --- Blog Management Routes ---

@app.route('/create_blog', methods=['GET'])
@login_required # Protect this route
def create_blog_form():
    """Renders the form for creating a new blog post."""
    # Pass current date for the publish date input field
    return render_template('admin_form.html', form_type='create', currentDate=date.today().isoformat())

@app.route('/edit_blog/<int:blog_id>', methods=['GET'])
@login_required # Protect this route
def edit_blog_form(blog_id):
    """Renders the form for editing an existing blog post."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            b.blog_id,
            b.heading,
            b.subheading,
            b.author,
            b.publish_date,
            b.content,
            i.image_filename,
            i.image_id AS thumbnail_image_id, # Get image_id for potential update
            i.alt_text
        FROM Blogs b
        LEFT JOIN Images i ON b.thumbnail_image_id = i.image_id
        WHERE b.blog_id = %s
    """, (blog_id,))
    blog = cursor.fetchone()
    conn.close()

    if blog:
        # Convert date object to string for HTML input type="date"
        if isinstance(blog['publish_date'], date):
            blog['publish_date'] = blog['publish_date'].isoformat()
        return render_template('admin_form.html', form_type='edit', blog=blog)
    else:
        flash('Blog post not found!', 'error')
        return redirect(url_for('admin'))

@app.route('/submit_blog', methods=['POST'])
@login_required # Protect this route
def submit_blog():
    """Handles the submission of a new blog post."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        heading = request.form['blogHeading']
        subheading = request.form.get('blogSubheading', '')
        author = request.form['blogAuthor']
        publish_date_str = request.form['blogDate'] # Name changed to 'blogDate' in admin_form.html
        content = request.form['blogContent']
        image_alt_text = request.form.get('imageAltText', f"Thumbnail for {heading}")

        thumbnail_file = request.files.get('blogImageUpload') # Name changed to 'blogImageUpload' in admin_form.html

        thumbnail_image_id = None
        if thumbnail_file and thumbnail_file.filename:
            # Save the image file
            filename = secure_filename(thumbnail_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            thumbnail_file.save(filepath)

            # Insert image into Images table
            cursor.execute("INSERT INTO Images (image_filename, alt_text) VALUES (%s, %s)",
                           (filename, image_alt_text))
            conn.commit()
            thumbnail_image_id = cursor.lastrowid # Get the ID of the newly inserted image

        # Insert blog post into Blogs table
        cursor.execute("""
            INSERT INTO Blogs (heading, subheading, author, publish_date, content, thumbnail_image_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (heading, subheading, author, publish_date_str, content, thumbnail_image_id))
        conn.commit()
        flash('Blog post added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred while adding blog post: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

@app.route('/update_blog/<int:blog_id>', methods=['POST'])
@login_required # Protect this route
def update_blog(blog_id):
    """Handles the update of an existing blog post."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        heading = request.form['blogHeading']
        subheading = request.form.get('blogSubheading', '')
        author = request.form['blogAuthor']
        publish_date_str = request.form['blogDate']
        content = request.form['blogContent']
        image_alt_text = request.form.get('imageAltText', f"Thumbnail for {heading}")

        thumbnail_file = request.files.get('blogImageUpload')
        current_thumbnail_id = request.form.get('currentThumbnailId') # Hidden input for existing image ID

        new_thumbnail_image_id = current_thumbnail_id
        if thumbnail_file and thumbnail_file.filename:
            # Save new image
            filename = secure_filename(thumbnail_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            thumbnail_file.save(filepath)

            if current_thumbnail_id:
                # Update existing image record with new filename and alt text
                cursor.execute("UPDATE Images SET image_filename = %s, alt_text = %s WHERE image_id = %s",
                               (filename, image_alt_text, current_thumbnail_id))
            else:
                # Insert new image record if no previous image
                cursor.execute("INSERT INTO Images (image_filename, alt_text) VALUES (%s, %s)",
                               (filename, image_alt_text))
                new_thumbnail_image_id = cursor.lastrowid # Get the ID of the newly inserted image
            conn.commit() # Commit image changes

        elif current_thumbnail_id:
            # If no new file but there was an old one, just update its alt text
            cursor.execute("UPDATE Images SET alt_text = %s WHERE image_id = %s",
                           (image_alt_text, current_thumbnail_id))
            conn.commit() # Commit alt text change


        # Update blog post in Blogs table
        cursor.execute("""
            UPDATE Blogs SET
                heading = %s,
                subheading = %s,
                author = %s,
                publish_date = %s,
                content = %s,
                thumbnail_image_id = %s
            WHERE blog_id = %s
        """, (heading, subheading, author, publish_date_str, content, new_thumbnail_image_id, blog_id))
        conn.commit()
        flash('Blog post updated successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'An error occurred while updating blog post: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_blog/<int:blog_id>', methods=['POST'])
@login_required # Protect this route
def delete_blog(blog_id):
    """Handles the deletion of a blog post and its associated image."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # First, get the thumbnail_image_id to potentially delete the image file and record
        cursor.execute("SELECT thumbnail_image_id FROM Blogs WHERE blog_id = %s", (blog_id,))
        result = cursor.fetchone()
        thumbnail_image_id = result[0] if result else None

        # Delete the blog post
        cursor.execute("DELETE FROM Blogs WHERE blog_id = %s", (blog_id,))

        if thumbnail_image_id:
            # Get filename before deleting image record
            cursor.execute("SELECT image_filename FROM Images WHERE image_id = %s", (thumbnail_image_id,))
            image_filename_result = cursor.fetchone()
            if image_filename_result and image_filename_result[0]:
                filename_to_delete = image_filename_result[0]
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
                if os.path.exists(filepath):
                    os.remove(filepath) # Delete the physical file
            # Delete the image record from the Images table
            cursor.execute("DELETE FROM Images WHERE image_id = %s", (thumbnail_image_id,))
        conn.commit()
        flash('Blog post deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting blog post: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))

# --- FAQ Management Routes (existing, kept for completeness) ---

@app.route('/delete_faq/<int:faq_id>', methods=['POST'])
@login_required # Protect this route
def delete_faq(faq_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM faqs WHERE faq_id = %s", (faq_id,))
        conn.commit()
        flash('FAQ deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting FAQ: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('admin'))




# --- Contact Form Submission Route ---
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    db_success = False
    admin_email_success = False
    user_email_success = False
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        job_title = request.form['job_title']
        company_name = request.form['company_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        industry = request.form['industry']
        num_employees = request.form['num_employees']
        additional_details = request.form.get('additional_details', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact_submissions (first_name, last_name, job_title, company_name, phone_number, email, industry, num_employees, additional_details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, job_title, company_name, phone_number, email, industry, num_employees, additional_details))
        conn.commit()
        conn.close()
        db_success = True
    except Exception as e:
        flash(f'An error occurred while submitting your message to the database: {e}', 'error')

    # Send email to admin
    try:
        admin_subject = f"New Contact Submission from {first_name} {last_name}"
        admin_body = f"""
        New contact submission received:\n
        Name: {first_name} {last_name}\n
        Job Title: {job_title}\n
        Company: {company_name}\n
        Phone: {phone_number}\n
        Email: {email}\n
        Industry: {industry}\n
        Number of Employees: {num_employees}\n
        Additional Details: {additional_details}
        """
        send_email(ADMIN_EMAIL, admin_subject, admin_body)
        admin_email_success = True
    except Exception as e:
        flash(f'Failed to send notification email to admin: {e}', 'error')

    # Send confirmation to user
    try:
        user_subject = "Thank you for contacting FortiFund!"
        user_body = f"Dear {first_name},\n\nThank you for reaching out to FortiFund. We have received your submission and will get back to you soon.\n\nBest regards,\nThe FortiFund Team"
        send_email(email, user_subject, user_body)
        user_email_success = True
    except Exception as e:
        flash(f'Failed to send confirmation email to you: {e}', 'error')

    # Flash success messages
    if db_success:
        flash('Your message has been submitted successfully!', 'success')
    if admin_email_success:
        flash('Notification email sent to admin successfully.', 'success')
    if user_email_success:
        flash('Confirmation email sent to you successfully.', 'success')

    return redirect(url_for('index'))

# --- Other Pages (existing) ---

@app.route('/faqs')
def faqs():
    content = return_content()
    # The return_content() function now groups faqs by category
    return render_template('faqs.html', **content)

@app.route('/demo')
def demo():
    content = return_content()
    return render_template('demo-page.html', **content)

@app.route('/matchmaking')
def matchmaking():
    content = return_content()
    return render_template('matchmaking.html', **content)

@app.route('/upcommingSolutions')
def upcommingSolutions():
    content = return_content()
    return render_template('upcomming.html', **content)


@app.route('/api/booked_dates', methods=['GET'])
def api_booked_dates():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT meeting_date FROM demo_bookings")
    booked = cursor.fetchall()
    conn.close()
    # Return list of YYYY-MM-DD strings
    return jsonify([row['meeting_date'].strftime('%Y-%m-%d') for row in booked])

@app.route('/api/booked_dates_times', methods=['GET'])
def api_booked_dates_times():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT meeting_date, meeting_time FROM demo_bookings")
    booked = cursor.fetchall()
    conn.close()
    # Return as { 'YYYY-MM-DD': ['08:00', ...] }
    result = {}
    for row in booked:
        date = row['meeting_date'].strftime('%Y-%m-%d')
        time_ = row['meeting_time']
        if date not in result:
            result[date] = []
        result[date].append(time_)
    return jsonify(result)

@app.route('/book_demo', methods=['POST'])
def book_demo():
    data = request.form
    firm_name = data.get('firm_name')
    company_type = data.get('company_type')
    person_name = data.get('person_name')
    title = data.get('title')
    email = data.get('email')
    team_size = data.get('team_size')
    meeting_date = data.get('meeting_date')
    meeting_time = data.get('meeting_time')

    # Check if date+time is already booked
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as cnt FROM demo_bookings WHERE meeting_date = %s AND meeting_time = %s", (meeting_date, meeting_time))
    if cursor.fetchone()['cnt'] > 0:
        conn.close()
        flash('Selected date and time is already booked. Please choose another slot.', 'error')
        return redirect(url_for('demo'))

    # Generate a placeholder meeting link (replace with real API if needed)
    meeting_link = f'https://meet.jit.si/fortifund-demo-{meeting_date.replace("-", "")}-{meeting_time.replace(":", "")}'

    # Save booking
    cursor.execute("""
        INSERT INTO demo_bookings (firm_name, company_type, person_name, title, email, team_size, meeting_date, meeting_time, meeting_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (firm_name, company_type, person_name, title, email, team_size, meeting_date, meeting_time, meeting_link))
    conn.commit()
    conn.close()

    # Send simple confirmation email (no link)
    subject = "Your Forti-Fund Demo Booking Confirmation"
    body = f"""
    Dear {person_name},\n\nYour demo is booked for {meeting_date} at {meeting_time}.\nWe will send you the meeting link shortly before your scheduled time.\n\nThank you!\nForti-Fund Team
    """
    send_email(email, subject, body)
    flash('Demo booked successfully! Confirmation sent to your email.', 'success')
    return redirect(url_for('demo'))

# --- APScheduler job to send meeting links at the correct time ---
def send_due_meeting_links():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Find bookings for today, within the next 10 minutes, and not yet sent
    now = time.strftime('%Y-%m-%d %H:%M')
    cursor.execute("SELECT * FROM demo_bookings WHERE CONCAT(meeting_date, ' ', meeting_time) >= %s AND CONCAT(meeting_date, ' ', meeting_time) <= DATE_ADD(%s, INTERVAL 10 MINUTE)", (now, now))
    bookings = cursor.fetchall()
    for booking in bookings:
        # Check if already sent (could add a sent flag in DB, for now just send)
        subject = "Your Forti-Fund Demo Meeting Link"
        body = f"Dear {booking['person_name']},\n\nHere is your meeting link for your demo scheduled at {booking['meeting_date']} {booking['meeting_time']}:\n{booking['meeting_link']}\n\nThank you!\nForti-Fund Team"
        send_email(booking['email'], subject, body)
        send_email(ADMIN_EMAIL, f"Demo Meeting Link for {booking['person_name']}", f"Meeting for {booking['person_name']} ({booking['email']}) at {booking['meeting_date']} {booking['meeting_time']}: {booking['meeting_link']}")
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(send_due_meeting_links, 'interval', minutes=5)
scheduler.start()


if __name__ == '__main__':
    # Ensure upload folder exists using the absolute path
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(debug=True)