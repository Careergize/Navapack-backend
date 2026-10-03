# Customer follow-up notifications

The existing `.env` is neither created nor changed. No real messages are sent during tests.

## Source code

- `marketing/models.py`: `FollowupNotification`, one durable delivery per pipeline, original follow-up date, notification type, recipient and channel.
- `marketing/migrations/0005_followupnotification.py`: database migration.
- `marketing/notifications.py`: recipient resolution, email service, Meta WhatsApp adapter, claim and delivery processing.
- `marketing/templates/marketing/followup_email.txt` and `.html`: email templates for upcoming, due, missed and escalation messages.
- `marketing/management/commands/send_followup_notifications.py`: scheduler command.
- `marketing/admin.py`: read-only delivery history (normal Django admin model permissions apply).
- `marketing/serializers.py`, `views.py`, `permissions.py`, `urls.py`: paginated management-only `GET /api/followup-notifications/`.
- `marketing/test_notifications.py`, `navapackbackend/test_settings.py`: isolated automated tests.

## Ownership and management configuration

1. Link each active `Salesperson.user` in Django Admin. Both Sales and Marketing employees use the existing Salesperson model. Its department must be Sales or Marketing (case insensitive).
2. Use the linked active user's email, falling back to `Salesperson.email` if blank. WhatsApp uses `Salesperson.phone`; Auth.Profile has no phone field. Customer telephone is never a notification destination.
3. Legacy unlinked records require exactly one active, approved user whose full name or username matches `Salesperson.name` exactly (case insensitive) AND whose `Profile.department` matches. Ambiguous or missing matches are recorded as failures rather than sent to another employee.
4. Add managers to the existing Django `Management` group and set their `Profile.department` or active `Salesperson.department`. All active matching department managers receive individual missed-follow-up escalation emails. Staff/superuser status grants history API access but does not by itself identify a department manager. There is no reporting-manager relation in the current schema.
5. Missing manager mappings are recorded as failed escalation deliveries. No credentials or recipients are hardcoded.

## Completion

Set the existing `CustomerPipeline.followup_status` to `COMPLETED` after completing a scheduled follow-up. Completed records and Won/Lost deals are excluded. DailyActivity has interaction notes but no marker associating a completed interaction with a particular scheduled follow-up, so simply recording an activity does not suppress reminders. No new completion field is added.

When scheduling another follow-up, update `next_followup_date`, `next_action` and reset `followup_status` to `PENDING`. Existing CRM APIs are unchanged. A different date creates a new notification cycle. Moving back to an already notified date reuses that date's history and will not resend successful deliveries.

## Existing environment file settings

Add/configure these in your existing deployment environment where necessary:

```text
EMAIL_BACKEND                 # optional; defaults to Django SMTP backend
EMAIL_HOST
EMAIL_PORT                    # default 587
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS                 # default True
EMAIL_USE_SSL                 # default False; do not enable both SSL and TLS
EMAIL_TIMEOUT                 # default 20 seconds
DEFAULT_FROM_EMAIL            # defaults to EMAIL_HOST_USER
TIME_ZONE                     # defaults to existing UTC; choose your business timezone
WHATSAPP_PROVIDER             # explicitly set meta for the supplied adapter
WHATSAPP_API_URL              # full HTTPS Meta /messages endpoint
WHATSAPP_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID  # read for future administration; not required for sending
WHATSAPP_TEMPLATE_LANGUAGE    # default en_US; must match approved templates
WHATSAPP_TEMPLATE_UPCOMING
WHATSAPP_TEMPLATE_DUE
WHATSAPP_TEMPLATE_MISSED
WHATSAPP_TIMEOUT              # default 20 seconds
```

`WHATSAPP_API_URL` must be the full `https://graph.facebook.com/<supported-version>/<phone-number-id>/messages` URL; it also supports the literal `{phone_number_id}` placeholder. Choose a supported Graph version in your configuration. No provider was already configured in this project. Other providers fail explicitly until their adapter is implemented, rather than receiving a Meta payload accidentally.

Create three approved WhatsApp templates. Each must have four positional BODY text parameters in this order: employee name, customer company, follow-up date, next action. For example:

- Upcoming: `Hello {{1}}, customer {{2}} has an upcoming follow-up on {{3}}. Next action: {{4}}.`
- Due: `Hello {{1}}, customer {{2}} has a follow-up due today, {{3}}. Next action: {{4}}. Please complete it today.`
- Missed: `Hello {{1}}, customer {{2}} missed the follow-up scheduled for {{3}}. Next action: {{4}}. Please complete the pending follow-up.`

See [Meta's template message reference](https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive). Credentials remain backend-only. Phone numbers must include their country code.

## Migration and EC2 scheduling

In the deployed application's virtual environment:

```bash
python manage.py migrate
python manage.py check
python manage.py send_followup_notifications --dry-run
python manage.py send_followup_notifications
```

The migration is already included; `makemigrations` is not necessary for deployment. Cron is suitable: this project has no Celery/Redis task queue. Run outside Gunicorn, which serves web requests and should not own scheduler threads. Set a cron entry with your actual EC2 application and virtual environment paths:

```cron
0 8 * * * cd /absolute/path/Navapack-backend && /absolute/path/venv/bin/python manage.py send_followup_notifications >> /absolute/path/followup-notifications.log 2>&1
```

Run cron as an account with project/environment access; ensure the log directory exists and is writable, and configure log rotation. Cron's trigger time follows the server timezone. The command's date follows Django `TIME_ZONE`. Install and enable cron on EC2; no cron job or production migration has been executed by this change.

## Delivery and retry behavior

For a follow-up on 10 October 2026: upcoming notifications on 8 October, due notifications on 10 October, missed notifications and manager emails from 11 October onward. The overdue query catches missed follow-ups after scheduler downtime. Upcoming and due notifications run only on their exact respective days.

PostgreSQL unique constraints and row locks prevent concurrent command runs from claiming the same delivery. `sent` means accepted by the SMTP backend/WhatsApp API, not confirmed arrival or reading; WhatsApp acceptance IDs are retained. Successful channels are skipped on reruns. Failed configuration/validation or explicit WhatsApp 4xx rejections retry while that notification type remains eligible.

A timeout, unexpected provider exception, or WhatsApp 5xx is `unknown`. A process crash after claiming leaves `sending`. Both are held for review, avoiding duplicate messages when acceptance cannot be determined. External SMTP and Meta delivery cannot guarantee exactly-once arrival. Check SMTP/provider records first; after confirming a message was NOT accepted, a trusted operator can reset only that row's status to `pending` using Django shell, then rerun the command while its date/type remains eligible. Never reset a `sent` row to retry another failed channel. Admin history is read-only to protect the ledger. No provider exception text or response body containing secrets is logged.

History uses separate channel rows, so email and WhatsApp status can be inspected independently. Error reasons, recipient, department, attempts and timestamps are visible to management. Scheduling/routing/database failures are logged by pipeline ID and exception class and processing continues with other customers.

## Verification

```bash
python manage.py test marketing Auth --settings=navapackbackend.test_settings
python manage.py makemigrations --check --dry-run --settings=navapackbackend.test_settings
```

Tests use a fresh in-memory SQLite database, local-memory email and mocked WhatsApp. They never connect to the production database or send live messages. PostgreSQL row-lock concurrency should additionally be smoke-tested in staging with two simultaneous command runs.

Use a staging record with follow-up date 2026-10-10 and safe test contacts. Date overrides below send real messages unless `--dry-run` is supplied:

```bash
python manage.py send_followup_notifications --date 2026-10-08 --dry-run
python manage.py send_followup_notifications --date 2026-10-10 --dry-run
python manage.py send_followup_notifications --date 2026-10-11 --dry-run
```

Automated tests cover two days before, due today, missed follow-up, manager department filtering, completed/Won/Lost suppression, repeated missed notifications, pending claims, email timeout with WhatsApp and other-customer continuation, WhatsApp timeout, explicit API rejection/retry, missing contacts/configuration, Sales/Marketing eligibility, inactive users, unique legacy name/department matching, missing managers, template payloads, dry runs and management API authorization. Check the existing record-security tests still pass.
