# Help Desk Ticketing System

A simple help desk ticketing system built with Flask, providing functionality for creating, viewing, and managing support tickets. The application supports user roles like admin, support, and regular users.

## Features

- User authentication and role-based access control.
- Create, view, and update support tickets.
- Assign tickets to support staff.
- Change ticket statuses and priorities.
- Comment on tickets.

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Steps

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

## Usage

### Accessing the Application

- Ensure your laptop and iPhone are on the same Wi-Fi network.
- Find your laptop’s local IP address (e.g., `192.168.1.5`).
- Open a web browser on your iPhone and visit `http://<laptop-ip>:5000` (e.g., `http://192.168.1.5:5000`).

### User Roles

- **Admin**: Can create, view, assign, and manage all tickets.
- **Support**: Can view and manage tickets assigned to them and view unassigned tickets.
- **User**: Can create tickets and view tickets they have created.

## Project Structure

```plaintext
helpdesk-ticketing-system/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── ticket_details.html
│   │   └── create_ticket.html
│   ├── static/
│   │   └── styles.css
│   └── config.py
│
├── migrations/
│
├── venv/
│
├── .flaskenv
├── requirements.txt
└── README.md
```

## Configuration

Configuration is managed through the `config.py` file in the `app/` directory. Ensure to update the database URI and other configurations as per your environment.
