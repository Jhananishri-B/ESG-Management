# EcoSphere: Enterprise ESG Management Platform

EcoSphere is a production-ready, enterprise-grade application built on **Odoo 18 Community Edition** for the Odoo Hackathon. It provides a comprehensive, beautifully designed platform for managing a corporation's Environmental, Social, and Governance (ESG) footprint.

Instead of a traditional ERP interface, EcoSphere brings a modern, premium SaaS aesthetic (resembling Microsoft 365 or Stripe Dashboard) with custom SCSS and interactive OWL components.

---

## 🌟 Key Features

The platform is split into decoupled, maintainable modules:

### 1. 🌍 Core & Environment (`ecosphere_core`, `ecosphere_environment`)
- **Central ESG Scoring Engine:** Automatically calculates aggregate E, S, and G scores across an unlimited, hierarchical department structure.
- **Carbon Tracking:** Logs energy usage, fleet emissions, and waste, auto-calculating CO2-equivalent footprints.
- **Goal Management:** Track corporate sustainability goals with real-time target versus actual metrics.

### 2. 🤝 Social Responsibility (`ecosphere_social`)
- **CSR Activity Tracking:** Plan and track community engagement and volunteer events.
- **Employee Participation:** Allow employees to log volunteer hours.
- **Health & Safety Incidents:** Integrated OSHA-style workplace incident tracking.

### 3. ⚖️ Governance & Compliance (`ecosphere_governance`)
- **Policy Lifecycle:** Create, version, and publish governance policies. Requires mandatory employee acknowledgement.
- **Audit Management:** Conduct internal and external ESG audits, record findings, and enforce corrective actions.
- **Risk Register:** Dynamic heat-mapped risk kanban board based on Likelihood × Impact.
- **Compliance Escalation:** Automated cron jobs escalate severe and unaddressed compliance issues to management.

### 4. 🎮 Gamification (`ecosphere_gamification`)
- **ESG Levels & XP:** Employees earn Experience Points (XP) for volunteering and completing challenges.
- **Reward Store:** A point-based shop where employees can redeem XP for company swag, extra time off, or charitable donations.
- **Dynamic Challenges:** Create individual or team-based sustainability challenges (e.g., "Zero Waste November").
- **Badges:** Auto-awarded achievements for hitting specific milestones.

### 5. 📊 Executive Dashboard (`ecosphere_dashboard`)
- **OWL Component Architecture:** Built using Odoo's frontend framework.
- **Real-Time Analytics:** Integrates Chart.js to visualize historical ESG trend data.
- **Leaderboards:** Pits departments against each other to foster healthy, sustainable competition.
- **Alerts:** Flags overdue policies and critical compliance issues directly on the homepage.

### 6. 📄 Reports & Portal (`ecosphere_reports`, `ecosphere_portal`)
- **Premium PDF Generation:** Custom QWeb PDF templates for generating Official Audit Reports and Department Scorecards.
- **Public Scorecard:** Exposes an aggregated, read-only ESG scorecard at `/esg` for public transparency.
- **Whistleblower Portal:** A secure, external web form at `/esg/report` for submitting anonymous compliance and ethics violations.

### 7. 🤖 AI Assistant (`ecosphere_ai`)
- **OpenAI Integration:** Connect your API key in Settings to unlock the ESG Copilot.
- **Policy Generator:** Auto-drafts comprehensive governance policies based on a simple prompt directly within the policy form. 
- *Note: Includes a fallback mock generator for demo environments without API keys.*

---

## 🛠️ Installation & Setup

1. **Clone the Repository** into your Odoo 18 addons path:
   ```bash
   git clone https://github.com/Jhananishri-B/ESG-Management.git
   ```
2. **Update Odoo Config**
   Ensure the directory is included in your `addons_path` in `odoo.conf`.
3. **Install Dependencies**
   If you have Python dependencies, install them. (EcoSphere relies mostly on native Odoo libraries and bundled JS).
4. **Update App List**
   Log into your Odoo database as an Administrator, activate **Developer Mode**, and click **Update Apps List**.
5. **Install EcoSphere**
   Search for "EcoSphere" in the Apps menu. You can install all modules at once by installing `ecosphere_dashboard`, or install them modularly as needed.
   
*Note: Installing the modules automatically loads rich demo data, allowing you to instantly explore the dashboard, risk registers, and gamification store without manual data entry.*

---

## 🎨 UI/UX Philosophy

EcoSphere completely overhauls the default dark/gray Odoo views. It introduces:
- **Clean Whitespace:** Bright, white backgrounds with soft `#f3f4f6` bordering.
- **Premium Typography:** Utilizes native OS sans-serif fonts with distinct font-weights for high legibility.
- **Dynamic Color Coding:**
  - 🟢 **Environmental:** Emerald Greens
  - 🔵 **Social:** Primary Blues
  - 🟣 **Governance:** Royal Purples
- **Micro-interactions:** Hover effects, soft shadows, and rounded kanban cards (`border-radius: 12px`).

---

## 🔒 Security & Access Rights
Three core security groups manage access across all modules:
1. **Employee (Read-Only/Basic):** Can view policies, log volunteer hours, view the reward store, and acknowledge documents.
2. **Manager (Operational):** Can create policies, conduct audits, approve rewards, and manage department goals.
3. **Admin (Full Access):** Can access configuration settings, configure AI keys, and delete records.

---

*Built with ❤️ for the Odoo Hackathon.*
