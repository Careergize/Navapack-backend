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

## Salesperson linking

Active users with an approved profile in the Sales department automatically
receive a linked salesperson when their user or profile is saved, including
approval through the API and edits in Django admin. Names fall back to email
or username when blank; duplicate names receive a user ID suffix. Existing
unlinked salesperson records are not automatically claimed by matching names
or emails.

Run `python manage.py migrate` during deployment to backfill existing approved
Sales users. Users without profiles need a profile with an employee ID,
department `Sales`, and approval first. Losing approval, leaving Sales, account
deactivation, or profile deletion deactivates the linked Sales salesperson while
preserving historical records. Bulk `QuerySet.update()` bypasses synchronization;
use individual model saves for profile/account changes.

## Department API

Departments are managed in Django admin and through these endpoints:

- `GET /api/departments/` — list departments (initial values: Sales, HR, Marketing)
- `POST /api/departments/` — create a department with `{"name": "Operations"}`
- `GET /api/departments/<id>/` — retrieve a department
- `PUT` / `PATCH /api/departments/<id>/` — update a department
- `DELETE /api/departments/<id>/` — delete a department

The migration also adds Sales, HR, and Marketing to the existing
`/api/lists/` department dropdown while preserving existing options.

## Customer contact email

Customer pipeline records also accept and return `estimated_price`, a decimal
amount with up to 15 digits and two decimal places (for example,
`"estimated_price": "1250.75"`). It defaults to `0.00` for existing records and
when omitted on creation. It is editable and visible in Django admin. The field
is stored independently of `estimated_value_ugx`; no total is calculated automatically.

Customer pipeline (`/api/pipeline/`) and daily activity (`/api/daily-activities/`)
records accept and return an optional `email` field, for example
`"email": "contact@example.com"`. POST, PUT, and PATCH validate email format;
omit it on creation or send `"email": ""` when no contact email is available.
Existing records receive an empty string after `python manage.py migrate`.
Both fields can be edited and searched in Django admin.

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
