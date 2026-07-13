# GymX Pro — Master Improvement Spec (Target: 8–10/10)

## Context
GymX Pro is a Flask gym-management app (members, trainers, membership plans,
workouts, attendance, progress, diet, notifications, reports) using
Flask + Flask-SQLAlchemy + Flask-Login + Flask-Migrate + Jinja/Bootstrap 5.
Current state: ~6/10. Clean architecture and real password hashing, but
critical gaps in security, functional completeness, and UI dynamism.
This document is the single source of truth for every change needed to
reach 8–10/10. Work it phase by phase — do not skip ahead; later phases
depend on earlier ones being solid.

---

## PHASE 1 — Security & Config (blocking, do first)

1. **Add CSRF protection.**
   - `CSRFProtect(app)` in `create_app()`.
   - Add `{{ csrf_token() }}` hidden field to every `<form>` in every template.
   - Prefer migrating raw HTML forms to `FlaskForm` classes (Flask-WTF is
     already a dependency) to get CSRF + server-side validation together.
   - **Done when:** every POST route rejects requests missing a valid token.

2. **Fix secrets & debug config.**
   - Generate a real `SECRET_KEY` (`secrets.token_hex(32)`), load from env var,
     never hardcode a default in source.
   - `FLASK_DEBUG` must default to `0`; only `1` in local `.env` (gitignored).
   - Confirm `.env` is in `.gitignore`; if a real secret was ever committed,
     rotate it.
   - **Done when:** no plaintext secret exists in any tracked file, and debug
     mode cannot accidentally ship to production.

3. **Fix the known `api.py` bug.**
   - `create_exercise()` passes `sets`/`reps`/`rest_seconds` — model fields
     are actually `default_sets`/`default_reps`/`default_rest_seconds`.
   - **Done when:** hitting the endpoint successfully creates a row, no
     `TypeError`.

4. **Server-side input validation everywhere.**
   - Replace bare `request.form.get()` usage with WTForms validators
     (`DataRequired`, `Email`, `Length`, `EqualTo`, `NumberRange` where
     relevant) on every form-handling route.
   - **Done when:** submitting empty/malformed data returns inline field
     errors, not a 500 or silent bad data in the DB.

5. **Authorization consistency pass.**
   - Replace ad-hoc `if current_user.role != 'admin':` checks with a shared
     `@role_required('admin', 'trainer')` decorator, applied to *every*
     route including all of `api.py` (currently some GET routes there have
     no role check at all — e.g. `/api/members` is readable by any logged-in
     member).
   - **Done when:** every route in every blueprint has an explicit,
     decorator-based role check, verified by a checklist pass over each
     blueprint file.

6. **Rate-limit auth.**
   - Add Flask-Limiter to the login route (e.g. 5 attempts / minute / IP).
   - **Done when:** repeated failed logins get throttled with a 429.

---

## PHASE 2 — Make the app actually dynamic (kill fake data)

7. **Wire the dashboard to real data.**
   - `dashboard.py` currently renders the template with zero variables —
     every stat and the "Recent Activity" table is hardcoded HTML.
   - Replace with real queries: active member count, today's check-ins,
     memberships expiring within 7 days, monthly revenue (sum of Payment
     rows this month), and a real "recent activity" feed (last 10
     attendance/membership/payment events, newest first).
   - **Done when:** creating a new member/attendance/payment immediately
     changes the dashboard numbers — no static content remains.

8. **Audit every other page for the same pattern.**
   - `reports/index.html` already does this correctly (`today_attendance`,
     `active_members`, `membership_plans` are real) — use it as the
     reference pattern and apply it everywhere else that currently has
     placeholder counts or sample rows.

---

## PHASE 3 — Full CRUD (currently Create+Read only, everywhere)

9. **Add Edit + Delete to every module**, following the members.py pattern
   already established for auth checks:
   - Members
   - Trainers
   - Membership Plans
   - Exercises
   - Workout Plans
   - Progress entries
   - Diet Plans
   - Notifications (delete/dismiss)
   - Use confirm-before-delete modals (not bare `<a href>` delete links —
     GET requests should never mutate state; delete must be POST/DELETE).
   - **Done when:** every entity list page has working Edit and Delete
     actions, each permission-checked and CSRF-protected.

10. **Finish Workout Plan ↔ Exercise linking.**
    - The `WorkoutPlanExercise` model exists and `workouts.py`'s `add()`
      route already fetches `Exercise.query.all()` — but `workouts/add.html`
      never uses it. Build the actual UI: exercise picker with sets/reps/
      order fields, saved as `WorkoutPlanExercise` rows on submit.
    - Add a workout plan detail view showing its linked exercises in order.
    - **Done when:** a trainer can build a full workout plan with ordered,
      configured exercises and see it rendered back correctly.

---

## PHASE 4 — UI/UX overhaul

11. **Extract CSS/JS out of `base.html`.**
    - Move the inline `<style>` block to `static/css/main.css`, organized
      by section (layout, components, forms, utilities).
    - Add `static/js/main.js` for shared interactivity.

12. **Mobile navigation.**
    - Sidebar currently disappears entirely below `md` breakpoint with no
      replacement. Add a Bootstrap offcanvas sidebar + hamburger trigger
      for mobile.

13. **List-view usability.**
    - Add pagination, search, and column sorting to Members, Exercises,
      Workout Plans, and any other `Model.query.all()` list view.
    - Add empty states ("No members yet — add your first one") instead of
      a bare empty table.

14. **Form UX.**
    - Inline field-level validation errors (paired with Phase 1 item 4),
      not just a generic top-of-page flash message.
    - Client-side instant feedback via `static/js/main.js` before submit,
      backed by the real server-side validation as the source of truth.

15. **AJAX where it matters.**
    - Convert high-frequency actions (attendance check-in/out, mark
      notification read, quick status toggles) to fetch-based partial
      updates instead of full page reloads.

16. **Dark mode toggle.**
    - The CSS variable system (`--primary`, `--dark`, `--light`, etc.)
      already exists in `:root` — add a `[data-theme="dark"]` override
      block and a toggle button; persist preference in a cookie/localStorage
      equivalent server-side setting if you want it to survive reload
      (note: browser storage is fine here since this is a real deployed
      site, not a sandboxed artifact).

17. **Accessibility pass.**
    - `aria-label` on all icon-only buttons (bell, avatar dropdown, etc.).
    - Fix the dead `href="#"` Profile link — build a real profile page.
    - Verify color contrast of `--warning`/`--danger` text against
      backgrounds meets WCAG AA.
    - Visible, well-styled focus rings on all interactive elements.

18. **Loading/error states.**
    - Skeleton loaders for dashboard/report stat cards while data loads
      (relevant once any of this is AJAX-driven).
    - Proper 404 and 403 error pages (currently only 500 is handled),
      styled consistently with the rest of the app.

---

## PHASE 5 — Testing & quality

19. **Expand `test_app.py`** to actually cover the risk surface:
    - Auth flow (register, login, logout, bad credentials).
    - Permission denial for every role on at least one route per blueprint.
    - Full CRUD cycle (create → edit → delete) for at least Members and
      Workout Plans.
    - CSRF rejection test (POST without token should fail).

20. **Add logging.**
    - Replace `print(traceback.format_exc())` in the 500 handler with
      Python's `logging` module, configured for both console (dev) and
      file/rotating handler (prod).

21. **CI.**
    - Simple GitHub Actions workflow: install deps, run `pytest` on every
      push/PR.

---

## PHASE 6 — Deployment readiness

22. **Production DB path.**
    - Confirm the MySQL path (`PyMySQL` is already a dependency) actually
      works end-to-end via `Flask-Migrate`, not just SQLite dev defaults.

23. **WSGI + process config.**
    - Add a `Procfile`/gunicorn config, document required env vars in
      `README.md`.

24. **Security headers.**
    - Add Flask-Talisman (or equivalent) for HSTS, CSP, and other baseline
      headers.

25. **Update `README.md`** to reflect actual current state once the above
    is done — right now it both undersells (Progress/Diet are marked
    "Planned" but already work) and oversells (Dashboard/Reports implied
    complete when Dashboard was 100% hardcoded) what's implemented.

---

## Execution notes for Antigravity

- Work phase by phase, in order — 3 and 4 depend on 1 and 2 being done
  first (CRUD forms need CSRF; dynamic dashboard data feeds the stats
  the UI phase will make skeleton-load).
- Use **Editor view** for Phase 1 (security-sensitive, review every line).
- Use **Manager view** to parallelize independent chunks of Phase 3/4
  (e.g. one agent on Members CRUD, one on Exercises CRUD, one on mobile
  nav — they touch mostly disjoint files).
- Ask for a pytest test alongside every phase's code, not as a separate
  pass at the end.
- Review every generated Artifact/screenshot before accepting — confirm
  it's showing real DB-backed data, not another hardcoded mock.

## Definition of "8–10/10"

- **8/10:** Phases 1–3 complete (secure, fully dynamic, full CRUD).
- **9/10:** + Phase 4 (UI overhaul feels like a real product, mobile-usable).
- **10/10:** + Phases 5–6 (tested, logged, CI'd, deployment-ready).
