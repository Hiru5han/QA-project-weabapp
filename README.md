Here’s an updated version of your **README** file, incorporating additional information such as **night mode**, **mobile support**, and further detail on the system features and setup:

---

# **Help Desk Ticketing System**

A comprehensive help desk ticketing system built with Flask, offering role-based access for managing IT support tickets. The system is fully responsive, includes night mode support, and enables admins, support staff, and regular users to efficiently handle support requests.

---

## **Features**

- **User Authentication and Role-Based Access Control**: Secure login system with role-specific permissions for Admins, Support Staff, and Regular Users.
- **Create, View, Update, and Manage Support Tickets**: Users can submit tickets and track their progress, with full support for changing statuses and priorities.
- **Assign Tickets to Support Staff**: Admins can assign tickets to the appropriate support team members.
- **Comment System**: Users can comment on tickets, providing real-time updates and communication.
- **Full Night Mode**: Users can toggle between light and dark modes to reduce eye strain during low-light conditions.
- **Mobile-Friendly**: The application is fully responsive and optimised for mobile devices, making it easy to manage tickets on the go.

---

## **Installation**

### **Prerequisites**

- **Python 3.8+**
- **pip** (Python package installer)

### **Steps**

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/helpdesk-ticketing-system.git
   cd helpdesk-ticketing-system
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the Database**

   ```bash
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```

5. **Run the Application**

   ```bash
   flask run --host=0.0.0.0
   ```

---

## **Usage**

### **Accessing the Application**

- Ensure your laptop and mobile device are on the same Wi-Fi network.
- Find your laptop’s local IP address (e.g., `192.168.1.5`).
- Open a web browser on your mobile device and visit `http://<laptop-ip>:5000` (e.g., `http://192.168.1.5:5000`).

### **User Roles**

- **Admin**: Can create, view, assign, and manage all tickets. They can also delete tickets and manage user accounts.
- **Support Staff**: Can view and manage tickets assigned to them, as well as take responsibility for unassigned tickets.
- **Regular User**: Can create tickets and view the status of tickets they’ve submitted.

---

## **Key Features**

- **Night Mode**: Toggle between light and dark mode for ease of use in low-light environments, reducing eye strain.
- **Mobile-Friendly Design**: The system is fully responsive and adapts seamlessly to mobile devices, allowing users to create, view, and manage tickets from anywhere.
- **Comment System**: Real-time communication on tickets, with comments logged for every ticket to ensure updates are captured.

---

## **Project Structure**

```plaintext
helpdesk-ticketing-system/
│
├── README.md               # Documentation for the project
├── app/                    # Main application package
│   ├── __init__.py         # Initializes the Flask application
│   ├── models.py           # Database models (User, Ticket, Comment)
│   ├── routes.py           # Application routes and logic
│   ├── static/             # Static assets (CSS, JavaScript, images)
│   │   ├── favicon.ico
│   │   ├── logo.png
│   │   ├── profile_images/ # Folder for storing user profile images
│   │   ├── styles.css      # Main stylesheet
│   │   └── theme-toggle.js # JavaScript for theme toggle (light/dark mode)
│   ├── templates/          # HTML templates for rendering views
│   │   ├── all_tickets.html
│   │   ├── assign_ticket.html
│   │   ├── assigned_tickets.html
│   │   ├── base.html
│   │   ├── closed_tickets.html
│   │   ├── create_ticket.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── ticket_details.html
│   │   ├── ticket_details_readonly.html
│   │   ├── unassigned_tickets.html
│   │   └── update_profile.html
│   └── docs/               # Documentation-related files
│       ├── build/
│       └── source/
├── build/                  # Build files for documentation (auto-generated)
├── htmlcov/                # Test coverage reports in HTML format
│   ├── class_index.html
│   ├── index.html
│   ├── function_index.html
│   └── coverage reports for various files...
├── instance/               # Instance-specific configuration and database
│   ├── config.py           # Instance-specific configurations
│   └── helpdesk.db         # SQLite database
├── migrations/             # Alembic migration scripts
│   ├── README
│   ├── alembic.ini         # Alembic configuration
│   ├── env.py              # Environment setup for migrations
│   ├── versions/           # Versioned migration scripts
│       └── 0deaae28b6fd_initial_migration.py
├── requirements.txt        # Python dependencies for the project
├── reset_db.py             # Script to reset the database
├── run.py                  # Entry point for running the Flask application
├── source/                 # Source files for documentation
├── test/                   # Unit tests for the application
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── templates/          # Unit tests for templates
│   │   ├── test_all_tickets_html.py
│   │   └── test_assigned_tickets.py
│   └── test_config.py      # Test for configuration
```

---

## **Configuration**

Configuration is managed through the `config.py` file located in the `app/` directory. Key settings include:

- **Database URI**: Define the URI for the database (SQLite or other).
- **Flask Environment Settings**: Set up environment variables, secret keys, and other configuration options.

---

### **Running the Application on a Mobile Device**

To access the application from a mobile device:

1. Ensure both the laptop and mobile device are connected to the same network.
2. On your laptop, run the Flask application using:
   ```bash
   flask run --host=0.0.0.0
   ```
3. Find your laptop’s local IP address (e.g., `192.168.1.5`).
4. Open your mobile browser and visit: `http://<laptop-ip>:5000`.

---

This updated README provides a more detailed overview of the Help Desk Ticketing System, its features, and the steps to set up and run the application. Let me know if you'd like any further adjustments!
