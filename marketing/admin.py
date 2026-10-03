from django.contrib import admin
from auditlog.models import LogEntry
from .models import (
    Salesperson,
    CustomerPipeline,
    DailyActivity,
    DropdownLists,
    ProductService,
    SalesStage,
    ActivityType,
    Unit,
    Department,
)


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'email',
        'phone',
        'department',
        'is_active',
    )


@admin.register(CustomerPipeline)
class CustomerPipelineAdmin(admin.ModelAdmin):
    list_display = (
        'prospect_id',
        'customer_company',
        'salesperson',
        'sales_stage',
        'probability_pct',
    )
    search_fields = (
        'prospect_id',
        'customer_company',
        'contact_person',
    )
    list_filter = (
        'sales_stage',
        'followup_status',
    )


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'salesperson',
        'customer_company',
        'activity_type',
    )
    search_fields = (
        'customer_company',
        'contact_person',
    )


admin.site.register(DropdownLists)
admin.site.register(ProductService)
admin.site.register(SalesStage)
admin.site.register(ActivityType)
admin.site.register(Unit)
admin.site.register(Department)


# Audit log
admin.site.unregister(LogEntry)

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'actor',
        'action',
        'content_type',
        'object_repr',
    )

    list_filter = (
        'action',
        'content_type',
    )

    search_fields = (
        'object_repr',
        'object_id',
    )

    readonly_fields = (
        'timestamp',
        'actor',
        'action',
        'content_type',
        'object_id',
        'object_repr',
        'changes',
        'remote_addr',
    )

