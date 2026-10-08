from django.contrib import admin
from .models import FollowupNotification


@admin.register(FollowupNotification)
class FollowupNotificationAdmin(admin.ModelAdmin):
    list_display = ('customer_pipeline', 'notification_type', 'scheduled_for',
                    'recipient_name', 'department', 'channel', 'status', 'created_at', 'updated_at')
    list_filter = ('notification_type', 'channel', 'status', 'department')
    search_fields = ('customer_pipeline__customer_company', 'recipient_name')
    readonly_fields = tuple(field.name for field in FollowupNotification._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
        'user',
        'email',
        'phone',
        'department',
        'is_active',
    )
    autocomplete_fields = ('user',)


@admin.register(CustomerPipeline)
class CustomerPipelineAdmin(admin.ModelAdmin):
    list_display = (
        'prospect_id',
        'customer_company',
        'email',
        'salesperson',
        'sales_stage',
        'probability_pct',
        'estimated_price',
    )
    search_fields = (
        'prospect_id',
        'customer_company',
        'contact_person',
        'email',
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
        'email',
        'activity_type',
    )
    search_fields = (
        'customer_company',
        'contact_person',
        'email',
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

