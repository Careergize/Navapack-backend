# CRM report downloads

These authenticated GET endpoints download the existing five-section report:

```text
/api/reports/export/excel/?from_date=2026-09-01&to_date=2026-09-30
/api/reports/export/pdf/?from_date=2026-09-01&to_date=2026-09-30
```

Send your existing `Authorization: Token <token>` header or use an authenticated Django session. Exports use the application's existing authenticated team-wide read access. Optional `salesperson=<id>` filters all five sections. Optional `limit=10` selects the number of top opportunities (1-100, default 10, consistent with the existing Reports API). It does not limit the other report sections.

Both dates are required in exact `YYYY-MM-DD` format. Invalid calendar dates, missing dates, reversed ranges and invalid optional numeric filters return HTTP 400 with an `error` property. Both range boundaries are included.

```json
{"error": "From date cannot be greater than To date."}
```

Successful responses return binary files, not JSON:

- Excel: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- PDF: `application/pdf`
- `Content-Disposition: attachment; filename="Navapack_Report_2026-09-01_to_2026-09-30.xlsx"` (or `.pdf`).

## Data and example format

`marketing/reports.py:build_report` is shared by the existing JSON endpoint and both exports. No models, migrations or new reporting calculations are introduced beyond applying the requested period to the existing overdue query. Existing JSON report defaults are preserved.

The reference workbook has five sections, matching the Reports API. Excel uses five corresponding sheets, with the reference's peach title, blue headers, per-salesperson KPI matrix, and matching detail columns:

1. Sales Performance
2. Top Opportunities
3. Market Intelligence
4. Management Delays
5. Orders Lost

Dates are real Excel date values. Currency cells are numeric with UGX formats. Headers are frozen, filters are available, columns are sized from content, and notes wrap. Customer text is written as literal strings to prevent accidental spreadsheet formulas. PDF uses the same data and columns, NAVAPACK / CRM REPORT headings, period labels, landscape A4, embedded fonts, repeated table headers and page numbers. Large salesperson matrices continue in groups of five employees. Long table rows can continue across pages.

There are no separate raw Customer Pipeline, Daily Activities or Won Orders sections in the current Reports API; those are not invented in the downloads. Won-order totals remain part of Sales Performance, as in the example.

## Date semantics

- Activity KPIs, intelligence and management delays: `DailyActivity.date` within the inclusive selected period.
- Won/lost orders: the existing current stage plus `CustomerPipeline.stage_last_updated` within the period.
- Samples: `last_contact_date` within the period, retaining the existing sample-status rules.
- Top opportunities: open deals with last contact, scheduled follow-up or latest stage update within the period, using the existing `touched_only` filter. The selected top-N ranking still uses potential value. Displayed future follow-up dates and management deadlines may be outside the period because they are properties of the included records.
- Overdue KPI in exports: scheduled follow-up date within the period and before `min(to_date, today)`. The JSON API keeps its existing broader snapshot behavior.

These are reports from current CRM records, not historical stage snapshots. The existing `stage_last_updated` uses `auto_now`, so a later record save may affect won/lost period membership. That existing model behavior is unchanged by the download feature.

## Deployment and tests

```bash
pip install -r requirements.txt
python manage.py check
```

Restart Gunicorn after deploying. No database migration or `.env` change is required.

For isolated tests (in-memory database, no production database or message delivery):

```bash
pip install -r requirements-test.txt
python manage.py test marketing Auth --settings=navapackbackend.test_settings
```

The download tests verify required/invalid/reversed dates, inclusive boundaries, period exclusions, file contents and MIME types, filenames, real Excel dates/currencies, correct KPI totals, reference sections, authentication, salesperson filtering, empty/same-day ranges, literal text, many employees and long notes. Regression coverage checks that the existing JSON API retains its snapshot defaults.

## Frontend download example

```javascript
async function downloadReport(format, fromDate, toDate, token) {
  const params = new URLSearchParams({from_date: fromDate, to_date: toDate});
  const response = await fetch(`/api/reports/export/${format}/?${params}`, {
    headers: {Authorization: `Token ${token}`},
  });
  if (!response.ok) {
    const body = await response.json();
    throw new Error(body.error || 'Report download failed.');
  }
  const extension = format === 'excel' ? 'xlsx' : 'pdf';
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = `Navapack_Report_${fromDate}_to_${toDate}.${extension}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
```

Use your existing backend base URL when the frontend is hosted on a different origin. Pass `excel` or `pdf`. The browser receives a file blob; no frontend report calculation is needed.

Library references: [openpyxl formatting](https://openpyxl.readthedocs.io/en/3.1/styles.html) and [ReportLab tables](https://docs.reportlab.com/reportlab/userguide/ch7_tables/).
