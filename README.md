# Navapack Backend

## Setup

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

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
