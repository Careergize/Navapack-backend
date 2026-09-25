from django.contrib import admin
from .models import (
    Salesperson,
    CustomerPipeline,
    DailyActivity,
    DropdownLists,
    ProductService,
    SalesStage,
    ActivityType,
    Unit,
)


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'department', 'is_active', 'created_at')
    list_filter = ('is_active', 'department')
    search_fields = ('name', 'email', 'phone')
    ordering = ('name',)


@admin.register(CustomerPipeline)
class CustomerPipelineAdmin(admin.ModelAdmin):
    list_display = (
        'prospect_id', 
        'customer_company', 
        'salesperson', 
        'sales_stage', 
        'estimated_value_ugx', 
        'next_followup_date', 
        'followup_status'
    )
    list_filter = (
        'sales_stage', 
        'salesperson', 
        'followup_status', 
        'customer_type', 
        'date_added'
    )
    search_fields = (
        'prospect_id', 
        'customer_company', 
        'contact_person', 
        'telephone', 
        'quotation_no'
    )
    date_hierarchy = 'date_added'
    readonly_fields = ('stage_last_updated',)
    fieldsets = (
        ('Basic Info', {
            'fields': (
                'prospect_id', 
                'date_added', 
                'salesperson', 
                'customer_company', 
                'location_town', 
                'contact_person', 
                'telephone', 
                'customer_type'
            )
        }),
        ('Product & Valuation', {
            'fields': (
                'product_service', 
                'requirement_specifications', 
                'estimated_quantity', 
                'unit', 
                'estimated_value_ugx'
            )
        }),
        ('Activity & Follow-up', {
            'fields': (
                'last_contact_date', 
                'last_discussion_feedback', 
                'next_action', 
                'next_followup_date', 
                'followup_status'
            )
        }),
        ('Sales Stage & Deals', {
            'fields': (
                'sales_stage', 
                'probability_pct', 
                'quotation_no', 
                'quotation_value_ugx', 
                'sample_trial_status', 
                'actual_order_value_ugx', 
                'stage_last_updated'
            )
        }),
        ('Outcome & Feedback Notes', {
            'fields': (
                'reason_lost', 
                'competitor_won_by', 
                'remarks_management_notes', 
                'corrective_action'
            )
        }),
    )


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = (
        'date', 
        'salesperson', 
        'customer_company', 
        'activity_type', 
        'prospect_status', 
        'order_received_value_ugx', 
        'cash_collected_ugx',
        'issue_status'
    )
    list_filter = (
        'activity_type', 
        'prospect_status', 
        'salesperson', 
        'issue_status', 
        'date'
    )
    search_fields = (
        'customer_company', 
        'contact_person', 
        'area_route_visited', 
        'discussion_outcome'
    )
    date_hierarchy = 'date'
    autocomplete_fields = ['customer_pipeline', 'salesperson']
    
    fieldsets = (
        ('Log Info', {
            'fields': (
                'date', 
                'salesperson', 
                'customer_pipeline', 
                'customer_company', 
                'area_route_visited', 
                'specific_location', 
                'prospect_status', 
                'contact_person', 
                'telephone'
            )
        }),
        ('Interaction Log', {
            'fields': (
                'product_service', 
                'activity_type', 
                'requirement_estimated_volume', 
                'discussion_outcome', 
                'next_action', 
                'next_followup_date'
            )
        }),
        ('Financial Logs', {
            'fields': (
                'quotation_submitted_value_ugx', 
                'order_received_value_ugx', 
                'cash_collected_ugx'
            )
        }),
        ('Intelligence & Escalations', {
            'fields': (
                'market_competitor_intelligence', 
                'management_support_needed', 
                'responsible_person_dept', 
                'required_by_date', 
                'issue_status'
            )
        }),
    )


@admin.register(DropdownLists)
class DropdownListsAdmin(admin.ModelAdmin):
    list_display = ('id', 'products_services', 'customer_types', 'sales_stages', 'departments')
    
    def has_add_permission(self, request):
        # Allow creating only 1 instance for master dropdown config
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(ProductService)
class ProductServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(SalesStage)
class SalesStageAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

