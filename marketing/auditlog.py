from auditlog.registry import auditlog

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


auditlog.register(Salesperson)
auditlog.register(CustomerPipeline)
auditlog.register(DailyActivity)
auditlog.register(DropdownLists)
auditlog.register(ProductService)
auditlog.register(SalesStage)
auditlog.register(ActivityType)
auditlog.register(Unit)
auditlog.register(Department)