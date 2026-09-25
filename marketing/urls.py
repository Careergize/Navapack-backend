from django.urls import path
from . import views
from .reports import ReportAPIView, WeeklyReportAPIView, MonthlyReportAPIView
urlpatterns = [
    # Salespersons
    path('salespersons/', views.SalespersonListCreateAPIView.as_view(), name='salesperson-list-create'),
    path('salespersons/<int:pk>/', views.SalespersonDetailAPIView.as_view(), name='salesperson-detail'),

    # Customer Pipeline
    path('pipeline/', views.CustomerPipelineListCreateAPIView.as_view(), name='pipeline-list-create'),
    path('pipeline/<int:pk>/', views.CustomerPipelineDetailAPIView.as_view(), name='pipeline-detail'),

    # Daily Activities
    path('daily-activities/', views.DailyActivityListCreateAPIView.as_view(), name='daily-activity-list-create'),
    path('daily-activities/<int:pk>/', views.DailyActivityDetailAPIView.as_view(), name='daily-activity-detail'),

    # Lookup/master data
    path('product-services/', views.ProductServiceListCreateAPIView.as_view(), name='product-service-list-create'),
    path('product-services/<int:pk>/', views.ProductServiceDetailAPIView.as_view(), name='product-service-detail'),
    path('sales-stages/', views.SalesStageListCreateAPIView.as_view(), name='sales-stage-list-create'),
    path('sales-stages/<int:pk>/', views.SalesStageDetailAPIView.as_view(), name='sales-stage-detail'),
    path('activity-types/', views.ActivityTypeListCreateAPIView.as_view(), name='activity-type-list-create'),
    path('activity-types/<int:pk>/', views.ActivityTypeDetailAPIView.as_view(), name='activity-type-detail'),
    path('units/', views.UnitListCreateAPIView.as_view(), name='unit-list-create'),
    path('units/<int:pk>/', views.UnitDetailAPIView.as_view(), name='unit-detail'),

    # Reports & Analytics
    path('dashboard-metrics/', views.DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('weekly-report/', views.WeeklyReportAPIView.as_view(), name='weekly-report'),
    path('lists/', views.DropdownListsAPIView.as_view(), name='dropdown-lists'),
    path('reports/', ReportAPIView.as_view(), name='reports'),               # ?period=weekly|monthly, or start_date & end_date
    path('reports/weekly/', WeeklyReportAPIView.as_view()),
    path('reports/monthly/', MonthlyReportAPIView.as_view()),
]