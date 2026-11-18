# 💪 GYM BUDDY – Gym Management SaaS

> *Your Gym. Your Goals. One Smart Buddy.*

GYM BUDDY runs the day-to-day of a gym from one Streamlit app: QR check-ins, member registration, fees with PDF receipts, renewals, WhatsApp reminders, trainer workout and diet plans, owner reports, and a win-back list for members who stopped coming.

It works in two modes:

| Mode | When | Data |
|---|---|---|
| **Demo** | No Supabase credentials configured | Seeded sample gym, isolated per browser tab, resets when the tab closes |
| **Live** | `[supabase]` secrets are set | Your Supabase Postgres database, secured by Row Level Security |

---

## Who sees what

The sidebar only shows the pages a role can use.

| Role | Pages |
|---|---|
| **Owner** | Dashboard, Reports, Check-in desk, New member, Fees & receipts, Renewals, Members, Win-back, Coaching roster, Workout plans, Diet plans |
| **Front desk** | Dashboard, Check-in desk, New member, Fees & receipts, Renewals, Members, Win-back |
| **Trainer** | Dashboard, My athletes, Workout plans, Diet plans (only their assigned athletes) |
| **Member** | My dashboard (plan, streak, 30-day activity), My QR pass, My workouts, My diet |
| **Admin** | Platform console (all gyms, add a gym, user directory) plus every owner page |

### Demo accounts (demo mode only)

| Role | Email | Password |
|---|---|---|
| Owner | `owner@fitzone.in` | `owner123` |
| Front desk | `reception@fitzone.in` | `reception123` |
| Trainer | `vikram@fitzone.in` | `trainer123` |
| Member | `amit@gmail.com` | `member123` |
| Admin | `admin@gymbuddy.io` | `admin123` |

The login page has one-click buttons for each of these when running in demo mode.

---

## Run locally

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Run the app **from the project folder** so Streamlit picks up `.streamlit/config.toml` (theme and fonts).

Run the tests:

```bash
python -m unittest discover -s tests
```

---

## Connect Supabase (live mode)

1. Create a project at [supabase.com](https://supabase.com) (region `ap-south-1` Mumbai is closest for Indian gyms).
2. **SQL Editor** → run all of `database/schema.sql`. It creates 14 tables, triggers and Row Level Security policies.
3. **Authentication → Users → Add user**: create the staff and member logins (tick *Auto confirm*). For sample data, create the five emails listed at the top of `database/seed.sql`, then run that file. It looks the users up by email, so there are no UUIDs to paste.
4. For real accounts, edit each user's row in the `profiles` table to set `role` (`owner`, `receptionist`, `trainer`, `member`, `admin`) and `gym_id`. Members log in with the same email as their member record, or set `members.user_id`.
5. Add your credentials to `.streamlit/secrets.toml` (copy `secrets.toml.example`):

   ```toml
   [supabase]
   url = "https://your-project-ref.supabase.co"
   anon_key = "your-anon-public-key"
   ```

   `SUPABASE_URL` / `SUPABASE_ANON_KEY` in the environment or a `.env` file work too. Only the **anon** key is needed; never put the service-role key in the app.

---

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub (`.streamlit/secrets.toml`, `.env` and `venv/` are git-ignored).
2. At [share.streamlit.io](https://share.streamlit.io) → **Create app** → pick the repo, branch `main`, main file `app.py`, Python 3.11 or 3.12.
3. **Advanced settings → Secrets**: paste the `[supabase]` block above. Leave it empty to deploy in demo mode.
4. Deploy. Once it's up, sign in with one of your Supabase users (or a demo account).

---

## Project layout

```
app.py                  Entry point: theme, login, role-based st.navigation
views/                  One file per screen (home, members, register, attendance, fees,
                        renewals, my_members, workout, diet, reports, inactive, admin)
services/               Business logic, one module per domain; all DB access lives here
components/             UI helpers (ui.py), Plotly charts, QR pass + decoder, PDF receipts
utils/                  Supabase client/session, IST date helpers, validators, demo database
database/schema.sql     Tables, triggers and RLS (column names match services/)
database/seed.sql       Optional sample gym for a fresh Supabase project
assets/                 styles.css design system and logos
tests/                  unittest suite (runs against the demo database)
```

---

© 2026 GYM BUDDY. Built with Python, Streamlit and Supabase.
