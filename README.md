# Navapack Backend

## Setup

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Create a local `.env` file with your PostgreSQL connection settings
(`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`) before
running migrations.

After pulling changes, run `python -m pip install -r requirements.txt`
and `python manage.py migrate`. The requirements include
`django-auditlog==3.4.1`, which provides the `auditlog` module; migrations
create its database tables. Each developer installs dependencies in
their own Python environment.

## Department API

Departments are managed in Django admin and through these endpoints:

- `GET /api/departments/` — list departments (initial values: Sales, HR, Marketing)
- `POST /api/departments/` — create a department with `{"name": "Operations"}`
- `GET /api/departments/<id>/` — retrieve a department
- `PUT` / `PATCH /api/departments/<id>/` — update a department
- `DELETE /api/departments/<id>/` — delete a department

The migration also adds Sales, HR, and Marketing to the existing
`/api/lists/` department dropdown while preserving existing options.

## Product API

- `GET /api/products/` — list products
- `POST /api/products/` — create a product
- `GET /api/products/<id>/` — retrieve a product
- `PUT` / `PATCH /api/products/<id>/` — update a product
- `DELETE /api/products/<id>/` — delete a product

Example POST payload:

```json
{
  "name": "Sample box",
  "category": "Packaging",
  "categorySlug": "packaging",
  "description": "A durable sample box.",
  "tag": "popular",
  "imageUrl": "https://example.com/sample-box.jpg",
  "active": true
}
```
