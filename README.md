# 💪 GYM BUDDY – Complete Gym Management SaaS

> **Tagline:** *Your Gym. Your Goals. One Smart Buddy.*  
> **Commercial SaaS Edition** • Production-Ready Application

---

## 🌟 Executive Overview

**GYM BUDDY** is a commercial-grade Gym Management Software as a Service (SaaS) built specifically for gym owners, fitness clubs, and personal training studios. It replaces outdated offline registers and fragmented spreadsheets with a futuristic, multi-facility, cloud-powered management portal.

GYM BUDDY includes full multi-gym tenant isolation, Supabase PostgreSQL database architecture, Supabase Auth with Role-Based Access Control (RBAC), QR code attendance scanning, fee collection in Indian Rupees (₹) with PDF receipts, automated membership renewal management, customized weekly workout plans, 4-meal nutritional diet planners, executive owner analytics, and an automated inactive member retention engine with direct WhatsApp re-engagement.

---

## 🎨 Futuristic Dark UI Design System

Designed from the ground up to look like an expensive, high-end SaaS product:

| UI Accent | Hex Code | Visual Application |
|---|---|---|
| **Main Background** | `#090B14` | Ultra-deep cosmic canvas |
| **Secondary Background** | `#111525` | Layered surface backdrop |
| **Card Background** | `#171D30` | Glassmorphic floating surfaces |
| **Elevated Surface** | `#202940` | Interactive dialogs & hover states |
| **Electric Purple** | `#8B5CF6` | Primary brand identity & action buttons |
| **Neon Cyan** | `#06D6C9` | Telemetry badges & high-tech highlights |
| **Neon Lime** | `#A3FF5C` | Active statuses & revenue positive KPIs |
| **Electric Blue** | `#3B82F6` | Secondary gradients & navigation badges |
| **Pink Highlight** | `#EC4899` | Warning alerts & pending fee indicators |

---

## 🏗️ Architecture & 11 Primary Screens

The system covers four core operational roles plus a Platform Super-Admin console:

```
├── app.py                     [SCREEN 1: Futuristic Login Portal & Platform Admin Console]
├── pages/
│   ├── 1_Member.py            [SCREEN 2: Online Joining / Member Registration]
│   ├── 2_Attendance.py        [SCREEN 3: Member QR Pass & SCREEN 5: Front Desk Register]
│   ├── 3_Workout.py           [SCREEN 4: Workout Routine & Weekly Exercise Split]
│   ├── 4_Fees.py              [SCREEN 6: Fees Entry & Official PDF Receipt Generator]
│   ├── 5_Renewals.py          [SCREEN 7: Renewal Management (7, 15, 30-day buckets)]
│   ├── 6_My_Members.py        [SCREEN 8: Trainer Athlete Roster & Last Visit Tracking]
│   ├── 7_Diet_Plan.py         [SCREEN 9: 4-Meal Nutritional Diet Planner]
│   ├── 8_Daily_Report.py      [SCREEN 10: Owner Dashboard & Plotly Revenue Telemetry]
│   └── 9_Inactive_Members.py  [SCREEN 11: Inactive Member Recovery & WhatsApp Campaigns]
```

### 1. SCREEN 1 – LOGIN & SUPER-ADMIN (Shared & Admin)
- Full-screen dark futuristic background with electric purple and cyan glow.
- GYM BUDDY custom brand logo.
- 1-Click quick login buttons for all roles (Super-Admin, Owner, Receptionist, Trainer, Member).
- **Platform Super-Admin Feature:** Multi-tenant facility management, new gym provisioning, and global staff directory.

### 2. SCREEN 2 – ONLINE JOINING (Member Section)
- Multi-section registration: Personal Details, Address, Emergency Contacts.
- Interactive membership plan selector with automatic start and end date calculation.
- Initial fee collection logging with immediate unique Member ID (`GMB-YYYY-XXX`) generation.
- Real-time digital QR code pass issuance with instant download.

### 3. SCREEN 3 & 5 – QR ATTENDANCE (Member & Receptionist)
- **Member View:** Personal high-contrast QR pass, monthly workout count, and attendance history.
- **Receptionist View:** Integrated QR camera scanner, image upload scanner, and manual Member ID search.
- **Duplicate Prevention:** Automatically blocks double check-ins on the same calendar day.
- Daily check-in register with time, method (QR / Manual), and instant search.

### 4. SCREEN 4 – WORKOUT PLAN (Member & Trainer)
- **Member View:** Monday through Sunday weekly split with exercise cards, sets, reps, rest durations, and form instructions.
- **Trainer/Owner View:** Dynamic exercise builder to create or modify routines for any assigned member.

### 5. SCREEN 6 – FEES ENTRY (Receptionist Section)
- Search members by name, phone, or member code.
- Record payments with Indian Rupees (₹), payment methods (UPI, Cash, Bank Transfer), and UTR references.
- **PDF Receipt Generator:** Automatically produces downloadable, professional payment receipts built with ReportLab.

### 6. SCREEN 7 – RENEWAL MANAGEMENT (Receptionist Section)
- Automatic categorization: Expiring in ≤ 7 days, ≤ 15 days, ≤ 30 days, and Already Expired.
- 1-Click direct WhatsApp renewal reminder link with personalized Indian message templates.
- In-place renewal processing: select new plan, compute extended expiry, and log renewal fees.

### 7. SCREEN 8 – MY MEMBERS (Trainer Section)
- Displays only athletes assigned to the logged-in coach.
- Shows current plan, expiry date, days since last workout, and attendance history.
- Direct coach-to-athlete WhatsApp chat integration.
- Owners can allocate or reassign members between trainers.

### 8. SCREEN 9 – DIET PLAN (Trainer Section)
- Comprehensive nutrition planner organized into 4 structured meals:
  1. 🍳 Breakfast
  2. 🍛 Lunch
  3. 🍪 Evening Snacks
  4. 🍝 Dinner
- Dynamic food item builder with quantities, meal timings, cooking instructions, and macro notes.

### 9. SCREEN 10 – OWNER DASHBOARD / DAILY REPORT (Owner Section)
- Real-time greeting with Asia/Kolkata (IST) standard time.
- 6 core metric stat cards: Total Members, Active Passes, Today's Check-ins, Monthly Revenue, Today's Collection, Inactive Members.
- Interactive dark Plotly charts:
  - Daily Revenue Velocity bar chart (with neon cyan/purple gradients)
  - Monthly Revenue Aggregates
  - Gym Check-in Throughput spline chart
  - Membership Plan Distribution donut chart
  - Cumulative Member Growth Trajectory area chart

### 10. SCREEN 11 – INACTIVE / MISSING MEMBERS (Retention Engine)
- Customizable inactivity threshold slider (7 to 60 days).
- Inactivity brackets: 7–14 days, 15–30 days, 30+ days, and Never Attended.
- Direct WhatsApp re-engagement campaign launcher with motivating messages.
- Outreach feedback tracker (Pending, Contacted, Responded, Returned, Lost).

---

## ⚡ Demo Accounts (1-Click Ready)

The application includes high-fidelity pre-seeded data for **FitZone Premium Gym** in Bengaluru, Karnataka:

| Role | Email | Password | Primary Screen |
|---|---|---|---|
| **Platform Admin** | `admin@gymbuddy.io` | `admin123` | Multi-Tenant Admin Console |
| **Gym Owner** | `owner@fitzone.in` | `owner123` | Executive Daily Report & KPIs |
| **Front Desk** | `reception@fitzone.in` | `reception123` | QR Attendance & Fee Entry |
| **Fitness Coach** | `vikram@fitzone.in` | `trainer123` | Assigned Members & Workouts |
| **Gym Member** | `amit@gmail.com` | `member123` | Personal QR Pass & Diet Plan |

*Note: You can click the 1-Click Demo buttons on the login screen for instant credential filling.*

---

## 🚀 Quick Start & Installation

### 1. Clone & Set Up Virtual Environment

```bash
cd c:\Users\manis\Desktop\GymBuddy\gym-buddy

# Create Python 3.11+ virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Automated Tests

```bash
python -m unittest discover -s tests
```
*Expected: `Ran 14 tests ... OK`*

### 4. Run the Streamlit Application

```bash
streamlit run app.py
```

The application will start at `http://localhost:8501`.

---

## 🗄️ Supabase PostgreSQL Setup & Migration

### Step 1: Create Supabase Project
1. Log in to [supabase.com](https://supabase.com) and create a new project.
2. Choose a region close to your users (e.g., `ap-south-1` Mumbai).

### Step 2: Execute Schema & Seed
1. Go to the **SQL Editor** tab in the Supabase Dashboard.
2. Paste and run the entire contents of `database/schema.sql`.
   - Provisions 14 normalized tables with UUID primary keys.
   - Configures foreign keys, cascade rules, and automated updated_at triggers.
   - Establishes Row-Level Security (RLS) policies for multi-gym isolation.
3. Paste and run `database/seed.sql` to populate realistic Indian demo data.

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` or `.streamlit/secrets.toml`:

```toml
# .streamlit/secrets.toml
[supabase]
url = "https://your-project-id.supabase.co"
key = "your-anon-public-key"
service_role_key = "your-service-role-key"
```

> **Smart Offline Fallback:** If live Supabase credentials are not provided, GYM BUDDY seamlessly runs on its built-in in-memory high-fidelity database simulator so you can demonstrate the application anywhere offline!

---

## ☁️ Deployment Guide

### Deploying to Streamlit Community Cloud
1. Push this repository to GitHub.
2. Connect your GitHub account at [share.streamlit.io](https://share.streamlit.io).
3. Select your repository, branch `main`, and main file `app.py`.
4. In **Advanced Settings**, paste your Supabase keys under **Secrets**:
   ```toml
   [supabase]
   url = "https://your-project.supabase.co"
   key = "your-anon-key"
   ```
5. Click **Deploy!**

---

## 📜 Commercial SaaS Rights & License

Copyright © 2026 GYM BUDDY SaaS. All rights reserved.  
Built with Python, Streamlit, and Supabase.
