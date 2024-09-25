# **Help Desk Ticketing System**

A comprehensive help desk ticketing system built with Flask, offering role-based access for managing IT support tickets.
The system is fully responsive, includes night mode support, and enables admins, support staff, and regular users to efficiently handle support requests.

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
   git clone https://github.com/Hiru5han/QA-project-weabapp.git
   cd QA-project-weabapp
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

5. **(Optional) Reset and Populate the Database with Sample Data**

   You can use the `reset_db.py` script to wipe the database and populate it with sample tickets and users. This script includes pre-loaded profile images like "homer-profile.png", "bart-profile.png", and others.

   ```bash
   python reset_db.py
   ```

6. **Run the Application**

   ```bash
   flask run --host=0.0.0.0
   ```

---

## **Usage**

### **Accessing the Application**

- Ensure your laptop and mobile device are on the same Wi-Fi network.
- Find your laptop’s local IP address (e.g., `192.168.1.5`).
- Open your mobile browser and visit: `http://<laptop-ip>:5000`.

---

## **Running Tests**

This project includes unit tests located in the `test/` directory. The tests can be run using `pytest`. Additionally, HTML coverage reports are generated and stored in the `htmlcov/` directory.

1. **Run all tests**:

   ```bash
   pytest
   ```

2. **View test coverage**:

   After running the tests, open the `htmlcov/index.html` file in a browser to view the detailed test coverage report.

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
QA-project-weabapp/
│
├── README.md
├── SoftEng Design Doc.docx
├── app
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-312.pyc
│   │   ├── models.cpython-312.pyc
│   │   └── routes.cpython-312.pyc
│   ├── config.py
│   ├── docs
│   │   ├── build
│   │   │   ├── doctrees
│   │   │   └── html
│   │   │       ├── _sources
│   │   │       └── _static
│   │   └── source
│   │       ├── _static
│   │       └── _templates
│   ├── models.py
│   ├── routes.py
│   ├── static
│   │   ├── favicon.ico
│   │   ├── logo.png
│   │   ├── styles.css
│   │   ├── theme-toggle.js
│   │   └── uploads
│   │       └── profile_images
│   │           ├── default.jpg
│   │           ├── default_image
│   │           │   └── default.jpg
│   │           └── starting_user_profile_images
│   │               ├── bart-profile.png
│   │               ├── burns-profile.png
│   │               ├── doctor-profile.png
│   │               ├── homer-profile.png
│   │               ├── krusty-profile.png
│   │               ├── lisa-profile.png
│   │               ├── maggie-profile.png
│   │               ├── marge-profile.png
│   │               └── ralph-profile.png
│   ├── templates
│   │   ├── all_tickets.html
│   │   ├── assign_ticket.html
│   │   ├── assigned_tickets.html
│   │   ├── base.html
│   │   ├── closed_tickets.html
│   │   ├── create_ticket.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── ticket_details.html
│   │   ├── ticket_details_readonly.html
│   │   ├── unassigned_tickets.html
│   │   └── update_profile.html
│   ├── utils.py
│   └── views
│       ├── __init__.py
│       ├── active_tickets_view.py
│       ├── all_tickets_view.py
│       ├── assign_ticket_view.py
│       ├── assigned_tickets_view.py
│       ├── closed_tickets_view.py
│       ├── create_ticket_view.py
│       ├── delete_ticket_view.py
│       ├── index_view.py
│       ├── login_view.py
│       ├── logout_view.py
│       ├── register_view.py
│       ├── ticket_details_readonly_view.py
│       ├── ticket_details_view.py
│       ├── unassigned_tickets_view.py
│       ├── update_profile_view.py
│       └── update_status_view.py
├── build
├── htmlcov
│   ├── class_index.html
│   ├── coverage_html_cb_6fb7b396.js
│   ├── favicon_32_cb_58284776.png
│   ├── function_index.html
│   ├── index.html
│   ├── keybd_closed_cb_ce680311.png
│   ├── run_py.html
│   ├── status.json
│   ├── style_cb_8e611ae1.css
│   ├── z_36f028580bb02cc8___init___py.html
│   ├── z_36f028580bb02cc8_conftest_py.html
│   ├── z_36f028580bb02cc8_test_config_py.html
│   ├── z_5f5a17c013354698___init___py.html
│   ├── z_5f5a17c013354698_models_py.html
│   ├── z_5f5a17c013354698_routes_py.html
│   ├── z_cb9fd7c543aa674d_test_base_html_py.html
│   ├── z_cb9fd7c543aa674d_test_login_html_py.html
│   └── z_cb9fd7c543aa674d_test_register_html_py.html
├── instance
│   ├── config.py
│   └── helpdesk.db
├── migrations
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       ├── 0deaae28b6fd_initial_migration.py
│       └── b2c9f5207fcb_added_profile_image_column_to_user_model.py
├── requirements.txt
├── reset_db.py
├── run.py
├── source
│   ├── _static
│   └── _templates
├── test
│   ├── __init__.py
│   ├── conftest.py
│   ├── templates
│   │   ├── test_all_tickets_html.py
│   │   ├── test_assigned_tickets.py
│   │   └── test_base.py
│   ├── test_config.py
│   ├── test_files
│   │   └── profile.jpg
│   ├── test_routes.py
│   ├── tree.txt
│   └── views
│       ├── test_active_tickets_view.py
│       ├── test_all_tickets_view.py
│       ├── test_assign_ticket_view.py
│       ├── test_assigned_tickets_view.py
│       ├── test_closed_tickets_view.py
│       └── test_create_ticket_view.py
└── tree.txt
```
