from datetime import date
from django.core.management.base import BaseCommand
from marketing.notifications import process_followups


class Command(BaseCommand):
    help = 'Send customer follow-up reminders and missed-follow-up manager escalations.'

    def add_arguments(self, parser):
        parser.add_argument('--date', type=date.fromisoformat, help='Override local date (YYYY-MM-DD).')
        parser.add_argument('--dry-run', action='store_true', help='Count only; no sends or database writes.')

    def handle(self, *args, **options):
        self.stdout.write('Checking customer follow-ups...')
        stats = process_followups(options['date'], options['dry_run'])
        for key, label in [('upcoming', 'Upcoming reminders'), ('due', 'Due today'),
                           ('missed', 'Missed follow-ups'), ('email_sent', 'Email notifications sent'),
                           ('whatsapp_sent', 'WhatsApp notifications sent'),
                           ('already_notified', 'Already notified'), ('failed', 'Failed')]:
            self.stdout.write(f'{label}: {stats[key]}')
        self.stdout.write('Dry run completed.' if options['dry_run'] else 'Follow-up notification process completed.')
