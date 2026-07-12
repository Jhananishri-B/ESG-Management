# 🌍 EcoSphere - Odoo 18 ESG Management Platform

An enterprise-grade ESG (Environmental, Social, Governance) Management Platform built natively on Odoo 18. Transforms standard ERP operations into a dynamic, gamified sustainability engine. Designed exclusively for corporate sustainability tracking and employee engagement.

---

## 🚀 Key Features

### 🌱 1. Environmental: Emission Tracking & Goals
Monitor your firm's carbon footprint in real-time.
- **Carbon Transactions:** Log CO2 emissions by department or source (e.g. Flight travel, Scope 1 + 2 tracking).
- **Environmental Goals:** Set targets like "Carbon Neutral by 2027" or "Achieve 40% Renewable Energy" with dynamic progress bars.
- **Live Statistics:** At-a-glance KPI cards showing total generated carbon records, active goals, and achieved objectives.
- **Emission Tips:** Actionable, UI-integrated insights for employees to reduce their daily carbon footprint.

![Environmental Dashboard](file:///C:/Users/JHANANISHRI/.gemini/antigravity/brain/tempmediaStorage/media__1783859444972.png) 

### 🤝 2. Social: CSR & Employee Engagement
Foster a culture of giving back to society with interactive CSR campaigns.
- **CSR Campaigns:** Browse active company-sponsored CSR activities (Tree Plantation, E-Waste Collection, Blood Donation).
- **One-Click Joining:** Frictionless enrollment via the dashboard with real-time UI updates to "✓ Joined".
- **Engagement Tracking:** Deep integration into employee profiles to track total hours, challenges joined, and completed activities.

### 🛡️ 3. Governance: Policies, Audits & Compliance
Ensure complete regulatory alignment and risk management.
- **Policy Management:** Centralized hub for all ESG policies (Environmental Management, Anti-Corruption, Data Privacy).
- **Compliance Audits:** Log tracking for recent internal and external compliance audits across the organization.
- **Issue Tracking:** Severity-coded compliance issue tracker (Critical, Major, Minor) with resolution statuses and due dates.
- **Report Generation:** Quick export functionality to generate executive compliance reports.

### 🎮 4. ESG Gamification Command Center
Make sustainability deeply engaging through built-in game mechanics and social evidence.
- **Unified 8-Section Dashboard:** A complete command center unifying E, S, and G metrics into a premium dark-themed UI.
- **Live KPI Widgets:** Rapid insights into active challenges, policies, and carbon footprints fetched dynamically via ORM.
- **Activity Feed:** A chronological feed of recent employee CSR participation to drive social engagement.
- **Leaderboard & XP Engine:** Top 5 employee leaderboard displaying accumulated XP, Gamification Badges, and total CSR counts, complete with medals (🥇 🥈 🥉).
- **Dynamic Progress Summaries:** Overall progression tracking for company-wide goals.

![Gamification Dashboard Top](file:///C:/Users/JHANANISHRI/.gemini/antigravity/brain/tempmediaStorage/media__1783859942738.png)
![Gamification Dashboard Bottom](file:///C:/Users/JHANANISHRI/.gemini/antigravity/brain/tempmediaStorage/media__1783859947942.png)

---

## 🛠️ Technical Implementation Details
- **Odoo 18 Architecture:** Operates cleanly on `esg_db` with models built entirely on robust Odoo 18 standards (`models.Model`). 
- **Premium QWeb Frontend:** Leverages Odoo's QWeb templating with HTML5 data bindings and custom CSS for a beautiful glass-morphism aesthetic.
- **State-Driven UI:** Context-sensitive component rendering controls user flows (e.g., hiding "Join" buttons for already enrolled activities).
- **Performant ORM Queries:** Analytical dashboard reporting powered by highly optimized `search_count()` and Odoo domain groupings, ensuring near-instant load times with zero hardcoded values.

## 📊 Mock Data & Demo Readiness
EcoSphere ships with a comprehensive demo data set for immediate presentation:
- **6 Environmental Goals** mapped to active Carbon Transactions.
- **6 Active ESG Policies** aligned with ongoing Audits.
- **4 Live Compliance Issues** spanning all severity levels.
- Pre-populated Gamification metrics (Scores, Badges, and CSR Participation) for the Leaderboard.

## 🏃 Quick Start / Upgrading

To compile and load the latest updates into the Odoo container:
```bash
docker exec -u 0 odoo odoo -u ecosphere -d esg_db -r odoo -w odoo --db_host db --stop-after-init
docker restart odoo
```
Navigate to `http://localhost:8069/ecosphere/dashboard` to access the Command Center.