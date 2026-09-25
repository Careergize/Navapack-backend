from django.db import models
from django.utils import timezone


class Salesperson(models.Model):
    """Separate model for Sales Representatives."""
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, default='')
    phone = models.CharField(max_length=50, blank=True, default='')
    department = models.CharField(max_length=100, default='Sales')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Salespersons"

    def __str__(self):
        return self.name


class CustomerPipeline(models.Model):
    # Basic Info
    prospect_id = models.CharField(max_length=50, unique=True, db_index=True)
    date_added = models.DateField(default=timezone.now)
    
    # Linked Salesperson
    salesperson = models.ForeignKey(
        Salesperson,
        on_delete=models.PROTECT,
        related_name='pipeline_deals',
        db_index=True
    )
    
    customer_company = models.CharField(max_length=255, db_index=True)
    location_town = models.CharField(max_length=100, blank=True, default='')
    contact_person = models.CharField(max_length=100, blank=True, default='')
    telephone = models.CharField(max_length=50, blank=True, default='')
    customer_type = models.CharField(max_length=100, blank=True, default='')

    # Product & Value
    product_service = models.CharField(max_length=255, blank=True, default='')
    requirement_specifications = models.TextField(blank=True, default='')
    estimated_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, blank=True, default='')
    estimated_value_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Activity & Follow-up
    last_contact_date = models.DateField(blank=True, null=True)
    last_discussion_feedback = models.TextField(blank=True, default='')
    next_action = models.CharField(max_length=255, blank=True, default='')
    next_followup_date = models.DateField(blank=True, null=True)
    followup_status = models.CharField(max_length=50, default='PENDING')  # PENDING, DUE TODAY, OVERDUE, COMPLETED

    # Sales Stage & Quotation
    sales_stage = models.CharField(max_length=100, default='New Lead')  # New Lead, Requirement Identified, Quotation Sent, Negotiation, Won, Lost
    probability_pct = models.IntegerField(default=0)
    quotation_no = models.CharField(max_length=100, blank=True, default='')
    quotation_value_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sample_trial_status = models.CharField(max_length=100, blank=True, default='')
    actual_order_value_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Outcome & Management Notes
    reason_lost = models.CharField(max_length=255, blank=True, default='')
    remarks_management_notes = models.TextField(blank=True, default='')
    competitor_won_by = models.CharField(max_length=100, blank=True, default='')
    stage_last_updated = models.DateField(auto_now=True)
    corrective_action = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.prospect_id} - {self.customer_company} ({self.salesperson.name})"


class DailyActivity(models.Model):
    # Relation & Date
    date = models.DateField(default=timezone.now, db_index=True)
    
    # Linked Salesperson
    salesperson = models.ForeignKey(
        Salesperson,
        on_delete=models.PROTECT,
        related_name='daily_activities',
        db_index=True
    )
    
    customer_pipeline = models.ForeignKey(
        CustomerPipeline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )

    # Visit & Contact Details
    area_route_visited = models.CharField(max_length=150, blank=True, default='')
    customer_company = models.CharField(max_length=255, db_index=True)
    specific_location = models.CharField(max_length=255, blank=True, default='')
    prospect_status = models.CharField(max_length=50, default='Existing')  # New Prospect, Existing
    contact_person = models.CharField(max_length=100, blank=True, default='')
    telephone = models.CharField(max_length=50, blank=True, default='')

    # Interaction
    product_service = models.CharField(max_length=255, blank=True, default='')
    activity_type = models.CharField(max_length=100, default='Physical Visit')  # Physical Visit, Phone Call, Email
    requirement_estimated_volume = models.CharField(max_length=100, blank=True, default='')
    discussion_outcome = models.TextField(blank=True, default='')
    next_action = models.CharField(max_length=255, blank=True, default='')
    next_followup_date = models.DateField(blank=True, null=True)

    # Financials
    quotation_submitted_value_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    order_received_value_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_collected_ugx = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Intelligence & Management Escalations
    market_competitor_intelligence = models.TextField(blank=True, default='')
    management_support_needed = models.TextField(blank=True, default='')
    responsible_person_dept = models.CharField(max_length=100, blank=True, default='')
    required_by_date = models.DateField(blank=True, null=True)
    issue_status = models.CharField(max_length=50, default='Pending')  # Pending, In Progress, On Hold, Resolved

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.date} - {self.salesperson.name} ({self.customer_company})"


class DropdownLists(models.Model):
    """Stores managed select dropdown options for the frontend."""
    products_services = models.JSONField(default=list)
    customer_types = models.JSONField(default=list)
    sales_stages = models.JSONField(default=list)
    departments = models.JSONField(default=list)



stage_last_updated = models.DateField(default=timezone.localdate)
def save(self, *args, **kwargs):
    # 1) only bump the date when the sales stage really changes
    if self.pk:
        old_stage = (CustomerPipeline.objects.filter(pk=self.pk)
                     .values_list('sales_stage', flat=True).first())
        if old_stage is not None and old_stage != self.sales_stage:
            self.stage_last_updated = timezone.localdate()

    # 2) auto-generate prospect_id (the frontend never sends one, and the field is required + unique)
    creating_without_id = not self.prospect_id
    if creating_without_id:
        import uuid
        self.prospect_id = uuid.uuid4().hex[:12]   # temporary unique value
    super().save(*args, **kwargs)
    if creating_without_id:
        self.prospect_id = f'PR-{self.pk:04d}'
        super().save(update_fields=['prospect_id'])


class ProductService(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SalesStage(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ActivityType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Unit(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name