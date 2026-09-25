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

    # Reports & Analytics
    path('dashboard-metrics/', views.DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('weekly-report/', views.WeeklyReportAPIView.as_view(), name='weekly-report'),
    path('lists/', views.DropdownListsAPIView.as_view(), name='dropdown-lists'),
    path('reports/', ReportAPIView.as_view()),               # ?period=weekly|monthly, or start_date & end_date
    path('reports/weekly/', WeeklyReportAPIView.as_view()),
    path('reports/monthly/', MonthlyReportAPIView.as_view()),
]