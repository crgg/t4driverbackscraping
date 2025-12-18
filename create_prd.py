from fpdf import FPDF
import datetime

class PRD(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Product Requirements Document (PRD) - T4Alerts', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'{num}. {label}', 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

    def bullet_points(self, items):
        self.set_font('Arial', '', 11)
        for item in items:
            self.cell(5)
            self.cell(0, 6, f'- {item}', 0, 1)
        self.ln()

pdf = PRD()
pdf.alias_nb_pages()
pdf.add_page()

# Title Page info
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 10, f'Project Name: T4Alerts', 0, 1)
pdf.cell(0, 10, f'Date: {datetime.date.today()}', 0, 1)
pdf.cell(0, 10, f'Author: Antigravity AI', 0, 1)
pdf.ln(10)

# 1. Introduction
pdf.chapter_title(1, 'Introduction')
pdf.chapter_body(
    "T4Alerts is a centralized web application designed to replace the current notification system (Email, SMS, Slack). "
    "It aims to provide a secure and user-friendly interface for monitoring application logs and SSL certificate statuses "
    "for the T4App ecosystem."
)

# 2. Key Objectives
pdf.chapter_title(2, 'Key Objectives')
pdf.bullet_points([
    "Centralize verification and log monitoring for multiple web applications.",
    "Proactively monitor SSL certificate expirations with visual severity indicators.",
    "Provide analytics on recurrent errors to assist in troubleshooting.",
    "Secure access via JWT authentication."
])

# 3. Core Features & Requirements
pdf.chapter_title(3, 'Core Features & Requirements')

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, '3.1 Authentication', 0, 1)
pdf.chapter_body(
    "The system requires a secure login mechanism to restrict access to authorized personnel only."
)
pdf.bullet_points([
    "User Registration: Ability to create new admin users.",
    "Login: Secure login obtaining a JSON Web Token (JWT).",
    "Session Management: JWT must be used for authorization in all protected routes."
])

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, '3.2 Main Dashboard Structure', 0, 1)
pdf.chapter_body(
    "Upon logging in, the user will be presented with a main dashboard divided into two primary sections:"
)
pdf.bullet_points([
    "Log Alerts: For application error monitoring.",
    "SSL Alerts: For certificate expiration monitoring."
])

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, '3.3 Log Alerts Section', 0, 1)
pdf.chapter_body(
    "This section allows users to inspect logs collected from various applications. "
    "The data source will include the following applications as defined in the configuration:"
)
pdf.bullet_points([
    "GoTo Logistics (driverapp.goto-logistics.com)",
    "GoExperior (driverapp.goexperior.com)",
    "KLC T4App (klc.t4app.com)",
    "AccurateCargo T4App (accuratecargo.t4app.com)",
    "Broker GoTo Logistics (broker.goto-logistics.com)",
    "KLC Crossdock T4App (klccrossdock.t4app.com)"
])
pdf.chapter_body(
    "Functional Requirements:"
)
pdf.bullet_points([
    "Selector: Dropdown or menu to choose one of the 6 monitored applications.",
    "Log View: Display list of logs ordered by Date and Repetition count.",
    "Classification: Visual distinction or tabs for 'Errors' vs 'Uncontrolled Errors'.",
    "Detail View: Clicking a log should show the full details (traceback, context) similar to the current email reports."
])

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, '3.4 Analytics & Statistics', 0, 1)
pdf.chapter_body(
    "To help identify stability issues, the system will provide visual analytics for each application."
)
pdf.bullet_points([
    "Route: Dedicated analytics view per web application.",
    "Metric: Most recurrent 'Uncontrolled Errors' per day.",
    "Visualization: Bar chart displaying the frequency of specific error types over time.",
    "Goal: Quickly spot spikes in specific errors."
])

pdf.set_font('Arial', 'B', 11)
pdf.cell(0, 8, '3.5 SSL Alerts Section', 0, 1)
pdf.chapter_body(
    "A dedicated view to check the SSL health of all domains at a glance."
)
pdf.bullet_points([
    "List View: Show all domains with their expiration status.",
    "Visual Severity: Use the defined color coding (Red < 8 days, Mustard < 30 days, Green > 30 days).",
    "Actions: Option to trigger a manual re-check."
])

# 4. Technical Stack Proposal
pdf.chapter_title(4, 'Technical Stack Proposal')
pdf.bullet_points([
    "Frontend: React.js or Vue.js (SPA) for a responsive dashboard.",
    "Backend: Python (FastAPI or Flask) or Node.js.",
    "Database: PostgreSQL for storing users, historical logs, and analytics data.",
    "Authentication: JWT (JSON Web Tokens).",
    "Charting: Chart.js or Recharts for the analytics bar charts."
])

# 5. Non-Functional Requirements
pdf.chapter_title(5, 'Non-Functional Requirements')
pdf.bullet_points([
    "Performance: Log lists should load with pagination to handle large datasets effectively.",
    "Security: Passwords must be hashed (e.g., bcrypt). API endpoints must be protected behind JWT middleware.",
    "Reliability: The system should be highly available."
])

pdf.output('t4alerts_prd.pdf', 'F')
print("PDF Generated Successfully")
