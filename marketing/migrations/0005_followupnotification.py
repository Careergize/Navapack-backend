# Follow-up delivery ledger; verified against Django 5.2.17.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0004_salesperson_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='FollowupNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(max_length=20)),
                ('scheduled_for', models.DateField()),
                ('recipient_key', models.CharField(max_length=80)),
                ('recipient_name', models.CharField(blank=True, max_length=150)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('channel', models.CharField(choices=[('email', 'Email'), ('whatsapp', 'WhatsApp')], max_length=10)),
                ('destination', models.CharField(blank=True, max_length=254)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sending', 'Sending / review required'), ('sent', 'Accepted'), ('failed', 'Failed'), ('unknown', 'Unknown / review required')], default='pending', max_length=10)),
                ('error', models.CharField(blank=True, max_length=255)),
                ('provider_message_id', models.CharField(blank=True, max_length=255)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer_pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_notifications', to='marketing.customerpipeline')),
            ],
            options={
                'ordering': ['-created_at'],
                'constraints': [models.UniqueConstraint(fields=('customer_pipeline', 'notification_type', 'scheduled_for', 'recipient_key', 'channel'), name='unique_followup_delivery')],
            },
        ),
    ]
