# Hamid Ali Awan — Portfolio + Admin CMS

This version adds a protected admin panel for contact messages and projects.

## Admin panel

Open:

`/admin/login`

After login you can:

- View contact messages
- Add, edit, mark read, and delete messages
- Add, edit, update, and delete projects
- Change project order, tags, image, GitHub URL, and live demo URL
- View dashboard counts
- Return to the public portfolio

## Local setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=your-strong-password
set SECRET_KEY=your-random-secret
python app.py
```

Then open `http://127.0.0.1:5000`.

Without Supabase environment variables, local development uses `portfolio.db`.

## Vercel deployment — important

Vercel's filesystem is not a permanent database. Therefore, for the admin panel to keep messages/projects after deployment, use Supabase.

1. Create a Supabase project.
2. Open `supabase_schema.sql` in Supabase SQL Editor and run it.
3. In Vercel Project Settings → Environment Variables, add:
   - `SECRET_KEY`
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
4. For `SUPABASE_KEY`, use the server-side service-role key. Never put it in frontend JavaScript.
5. Redeploy the project.

The public contact form stores messages in the `messages` table. The admin panel reads and manages the same records.

## Important

Do not commit `.env` or real Supabase keys to GitHub.
