from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

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
from .serializers import (
    SalespersonSerializer,
    CustomerPipelineSerializer,
    DailyActivitySerializer,
    DropdownListsSerializer,
    ProductServiceSerializer,
    SalesStageSerializer,
    ActivityTypeSerializer,
    UnitSerializer,
)


# ==========================================
# 1. SALESPERSON API VIEWS
# ==========================================

class SalespersonListCreateAPIView(APIView):
    """List all active salespersons or create a new salesperson."""
    
    def get(self, request):
        salespersons = Salesperson.objects.filter(is_active=True)
        serializer = SalespersonSerializer(salespersons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SalespersonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalespersonDetailAPIView(APIView):
    """Retrieve, update, or delete a salesperson instance."""

    def get_object(self, pk):
        try:
            return Salesperson.objects.get(pk=pk)
        except Salesperson.DoesNotExist:
            return None

    def get(self, request, pk):
        salesperson = self.get_object(pk)
        if not salesperson:
            return Response({'error': 'Salesperson not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SalespersonSerializer(salesperson)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        salesperson = self.get_object(pk)
        if not salesperson:
            return Response({'error': 'Salesperson not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SalespersonSerializer(salesperson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        salesperson = self.get_object(pk)
        if not salesperson:
            return Response({'error': 'Salesperson not found'}, status=status.HTTP_404_NOT_FOUND)
        salesperson.is_active = False  # Soft delete
        salesperson.save()
        return Response({'message': 'Salesperson deactivated'}, status=status.HTTP_204_NO_CONTENT)


# ==========================================
# 2. CUSTOMER PIPELINE API VIEWS
# ==========================================

class CustomerPipelineListCreateAPIView(APIView):
    """List customer pipeline records or create a new deal."""

    def get(self, request):
        queryset = CustomerPipeline.objects.select_related('salesperson').all()
        
        # Filtering support
        salesperson_id = request.GET.get('salesperson')
        sales_stage = request.GET.get('sales_stage')
        search = request.GET.get('search')

        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)
        if sales_stage:
            queryset = queryset.filter(sales_stage=sales_stage)
        if search:
            queryset = queryset.filter(
                Q(customer_company__icontains=search) | 
                Q(contact_person__icontains=search) | 
                Q(prospect_id__icontains=search)
            )

        serializer = CustomerPipelineSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CustomerPipelineSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerPipelineDetailAPIView(APIView):
    """Retrieve, update, or delete a customer pipeline record."""

    def get_object(self, pk):
        try:
            return CustomerPipeline.objects.select_related('salesperson').get(pk=pk)
        except CustomerPipeline.DoesNotExist:
            return None

    def get(self, request, pk):
        pipeline = self.get_object(pk)
        if not pipeline:
            return Response({'error': 'Pipeline record not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerPipelineSerializer(pipeline)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        pipeline = self.get_object(pk)
        if not pipeline:
            return Response({'error': 'Pipeline record not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomerPipelineSerializer(pipeline, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        pipeline = self.get_object(pk)
        if not pipeline:
            return Response({'error': 'Pipeline record not found'}, status=status.HTTP_404_NOT_FOUND)
        pipeline.delete()
        return Response({'message': 'Pipeline record deleted'}, status=status.HTTP_204_NO_CONTENT)


# ==========================================
# 3. DAILY ACTIVITY API VIEWS
# ==========================================

class DailyActivityListCreateAPIView(APIView):
    """List daily logs or record a new daily activity."""

    def get(self, request):
        queryset = DailyActivity.objects.select_related('salesperson', 'customer_pipeline').all()

        salesperson_id = request.GET.get('salesperson')
        activity_type = request.GET.get('activity_type')
        search = request.GET.get('search')

        if salesperson_id:
            queryset = queryset.filter(salesperson_id=salesperson_id)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        if search:
            queryset = queryset.filter(
                Q(customer_company__icontains=search) | 
                Q(contact_person__icontains=search)
            )

        serializer = DailyActivitySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DailyActivitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DailyActivityDetailAPIView(APIView):
    """Retrieve, update, or delete a daily activity entry."""

    def get_object(self, pk):
        try:
            return DailyActivity.objects.select_related('salesperson', 'customer_pipeline').get(pk=pk)
        except DailyActivity.DoesNotExist:
            return None

    def get(self, request, pk):
        activity = self.get_object(pk)
        if not activity:
            return Response({'error': 'Activity log not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DailyActivitySerializer(activity)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        activity = self.get_object(pk)
        if not activity:
            return Response({'error': 'Activity log not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DailyActivitySerializer(activity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        activity = self.get_object(pk)
        if not activity:
            return Response({'error': 'Activity log not found'}, status=status.HTTP_404_NOT_FOUND)
        activity.delete()
        return Response({'message': 'Activity log deleted'}, status=status.HTTP_204_NO_CONTENT)


# ==========================================
# 4. DASHBOARD METRICS API VIEW
# ==========================================

class DashboardMetricsAPIView(APIView):
    """Computes all front-page dashboard statistics and salesperson performance matrix."""

    def get(self, request):
        today = timezone.now().date()

        # 1. Critical Actions
        overdue_followups = CustomerPipeline.objects.filter(
            next_followup_date__lt=today
        ).exclude(sales_stage__in=['Won', 'Lost']).count()

        due_today = CustomerPipeline.objects.filter(
            next_followup_date=today
        ).exclude(sales_stage__in=['Won', 'Lost']).count()

        no_date_set = CustomerPipeline.objects.filter(
            next_followup_date__isnull=True
        ).exclude(sales_stage__in=['Won', 'Lost']).count()

        # 2. Pipeline Health
        active_opps = CustomerPipeline.objects.exclude(sales_stage__in=['Won', 'Lost'])
        active_count = active_opps.count()
        total_pipeline_val = active_opps.aggregate(Sum('estimated_value_ugx'))['estimated_value_ugx__sum'] or 0
        quotations_pending = active_opps.filter(sales_stage='Quotation Sent').count()

        # 3. Monthly Performance
        start_of_month = today.replace(day=1)
        orders_won_mtd = CustomerPipeline.objects.filter(
            sales_stage='Won', stage_last_updated__gte=start_of_month
        )
        orders_won_count = orders_won_mtd.count()
        total_order_value = orders_won_mtd.aggregate(Sum('actual_order_value_ugx'))['actual_order_value_ugx__sum'] or 0

        monthly_activities = DailyActivity.objects.filter(date__gte=start_of_month)
        cash_collected = monthly_activities.aggregate(Sum('cash_collected_ugx'))['cash_collected_ugx__sum'] or 0

        # 4. Salesperson Pipeline Performance Matrix
        salespersons = Salesperson.objects.filter(is_active=True)
        matrix = []

        for sp in salespersons:
            sp_prospects = CustomerPipeline.objects.filter(salesperson=sp)
            sp_active = sp_prospects.exclude(sales_stage__in=['Won', 'Lost'])
            sp_won = sp_prospects.filter(sales_stage='Won')

            matrix.append({
                'salesperson_id': sp.id,
                'salesperson_name': sp.name,
                'total_prospects': sp_prospects.count(),
                'active_pipeline_value': sp_active.aggregate(Sum('estimated_value_ugx'))['estimated_value_ugx__sum'] or 0,
                'quotations_pending': sp_active.filter(sales_stage='Quotation Sent').count(),
                'orders_won_value': sp_won.aggregate(Sum('actual_order_value_ugx'))['actual_order_value_ugx__sum'] or 0,
                'overdue_followups': sp_active.filter(next_followup_date__lt=today).count(),
            })

        return Response({
            'critical_action': {
                'overdue_followups': overdue_followups,
                'due_today': due_today,
                'no_date_set': no_date_set,
            },
            'pipeline_health': {
                'active_opportunities': active_count,
                'total_pipeline_value': total_pipeline_val,
                'quotations_pending': quotations_pending,
            },
            'monthly_performance': {
                'orders_won_mtd': orders_won_count,
                'total_order_value_ugx': total_order_value,
                'cash_collected_ugx': cash_collected,
            },
            'salesperson_matrix': matrix,
        }, status=status.HTTP_200_OK)


# ==========================================
# 5. WEEKLY REPORT API VIEW
# ==========================================

class WeeklyReportAPIView(APIView):
    """Generates the 5-section weekly performance report within a date range."""

    def get(self, request):
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if not start_date_str or not end_date_str:
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())  # Monday
            end_date = start_date + timedelta(days=5)  # Saturday
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        activities = DailyActivity.objects.filter(date__range=[start_date, end_date])
        salespersons = Salesperson.objects.filter(is_active=True)

        # Section 1: KPI Matrix
        kpi_matrix = []
        metrics_list = [
            ('Physical Visits', lambda qs: qs.filter(activity_type='Physical Visit').count()),
            ('New Prospects Identified', lambda qs: qs.filter(prospect_status='New Prospect').count()),
            ('Existing Customer Visits', lambda qs: qs.filter(prospect_status='Existing').count()),
            ('Follow-up Interactions', lambda qs: qs.filter(activity_type='Phone Call').count()),
            ('Quotations Submitted (#)', lambda qs: qs.filter(quotation_submitted_value_ugx__gt=0).count()),
            ('Quotation Value (UGX)', lambda qs: qs.aggregate(Sum('quotation_submitted_value_ugx'))['quotation_submitted_value_ugx__sum'] or 0),
            ('Orders Confirmed (#)', lambda qs: qs.filter(order_received_value_ugx__gt=0).count()),
            ('Order Value Won (UGX)', lambda qs: qs.aggregate(Sum('order_received_value_ugx'))['order_received_value_ugx__sum'] or 0),
            ('Cash Collections (UGX)', lambda qs: qs.aggregate(Sum('cash_collected_ugx'))['cash_collected_ugx__sum'] or 0),
        ]

        for label, calc_fn in metrics_list:
            row = {'metric': label, 'per_salesperson': {}}
            total = 0
            for sp in salespersons:
                sp_acts = activities.filter(salesperson=sp)
                val = calc_fn(sp_acts)
                row['per_salesperson'][sp.name] = val
                total += val if isinstance(val, (int, float)) else 0
            row['total_team'] = total
            kpi_matrix.append(row)

        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'salespersons': [sp.name for sp in salespersons],
            'kpi_matrix': kpi_matrix,
            'top_opportunities': CustomerPipelineSerializer(
                CustomerPipeline.objects.exclude(sales_stage__in=['Won', 'Lost']).order_by('-estimated_value_ugx')[:10],
                many=True
            ).data,
            'market_intelligence': DailyActivitySerializer(
                activities.exclude(market_competitor_intelligence=''),
                many=True
            ).data,
            'management_delays': DailyActivitySerializer(
                activities.exclude(management_support_needed=''),
                many=True
            ).data,
            'orders_lost': CustomerPipelineSerializer(
                CustomerPipeline.objects.filter(sales_stage='Lost'),
                many=True
            ).data,
        }, status=status.HTTP_200_OK)


# ==========================================
# 6. DROPDOWN LISTS API VIEW
# ==========================================

class DropdownListsAPIView(APIView):
    """Retrieve or update option dropdown values."""

    def get_object(self):
        obj, _ = DropdownLists.objects.get_or_create(id=1)
        return obj

    def get(self, request):
        obj = self.get_object()
        serializer = DropdownListsSerializer(obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        obj = self.get_object()
        serializer = DropdownListsSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 7. MASTER LOOKUP API VIEWS
# ==========================================

class ProductServiceListCreateAPIView(APIView):
    def get(self, request):
        queryset = ProductService.objects.all().order_by('name')
        serializer = ProductServiceSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductServiceDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return ProductService.objects.get(pk=pk)
        except ProductService.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ProductService not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductServiceSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ProductService not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductServiceSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ProductService not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'ProductService deleted'}, status=status.HTTP_204_NO_CONTENT)


class SalesStageListCreateAPIView(APIView):
    def get(self, request):
        queryset = SalesStage.objects.all().order_by('name')
        serializer = SalesStageSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SalesStageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SalesStageDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return SalesStage.objects.get(pk=pk)
        except SalesStage.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'SalesStage not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SalesStageSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'SalesStage not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SalesStageSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'SalesStage not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'SalesStage deleted'}, status=status.HTTP_204_NO_CONTENT)


class ActivityTypeListCreateAPIView(APIView):
    def get(self, request):
        queryset = ActivityType.objects.all().order_by('name')
        serializer = ActivityTypeSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ActivityTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivityTypeDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return ActivityType.objects.get(pk=pk)
        except ActivityType.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ActivityType not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ActivityTypeSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ActivityType not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ActivityTypeSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'ActivityType not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'ActivityType deleted'}, status=status.HTTP_204_NO_CONTENT)


class UnitListCreateAPIView(APIView):
    def get(self, request):
        queryset = Unit.objects.all().order_by('name')
        serializer = UnitSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return Unit.objects.get(pk=pk)
        except Unit.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UnitSerializer(obj).data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UnitSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({'error': 'Unit not found'}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response({'message': 'Unit deleted'}, status=status.HTTP_204_NO_CONTENT)