"""
reports.py  -  Weekly / Monthly / Custom-range reports for the Navapack tracker.

Put this file next to views.py in your Django app, then wire the URLs (see SETUP.md).

Endpoints
---------
GET /api/reports/                                   -> weekly report for the current week
GET /api/reports/weekly/?date=2026-09-10            -> week (Mon-Sat) that contains that date
GET /api/reports/monthly/?month=2026-09             -> whole calendar month
GET /api/reports/?start_date=2026-09-01&end_date=2026-09-15   -> any custom range

Optional params on all of them:
    salesperson=<id>     limit the whole report to one rep
    limit=10             how many rows for "Top Active Opportunities"
    touched_only=true    Section 2: only deals with activity inside the period
"""
import calendar
from datetime import date, datetime, timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomerPipeline, DailyActivity, Salesperson

# The frontend uses "Order Won"/"Order Lost"; older backend code used "Won"/"Lost".
# Accept both so reports never silently return zero.
WON_STAGES = ['Order Won', 'Won']
LOST_STAGES = ['Order Lost', 'Lost']
CLOSED_STAGES = WON_STAGES + LOST_STAGES
SAMPLE_NOT_STARTED = ['', 'Not Started']
RESOLVED_STATUSES = ['resolved', 'completed', 'closed']

WEEK_LENGTH_DAYS = 5  # Monday + 5 = Saturday. Change to 6 if you want Mon-Sun.


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _num(value):
    """Decimal/None -> float so the JSON is plain numbers."""
    return float(value) if value is not None else 0


def _parse_date(value, field):
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        raise ValueError(f'{field} must be in YYYY-MM-DD format')


def resolve_period(params, default_period='weekly'):
    """
    Turn query params into (period_label, start_date, end_date).
    Priority: explicit start_date/end_date  >  monthly  >  weekly.
    """
    today = timezone.localdate()
    start_s, end_s = params.get('start_date'), params.get('end_date')

    if start_s or end_s:
        if not (start_s and end_s):
            raise ValueError('Provide both start_date and end_date')
        period = 'custom'
        start = _parse_date(start_s, 'start_date')
        end = _parse_date(end_s, 'end_date')
    else:
        period = (params.get('period') or default_period).lower()
        if period == 'monthly':
            month = params.get('month')
            if month:
                try:
                    year, mon = (int(x) for x in month.split('-'))
                    start = date(year, mon, 1)
                except (ValueError, TypeError):
                    raise ValueError('month must be in YYYY-MM format')
            else:
                start = today.replace(day=1)
            end = date(start.year, start.month, calendar.monthrange(start.year, start.month)[1])
        elif period == 'weekly':
            anchor = _parse_date(params['date'], 'date') if params.get('date') else today
            start = anchor - timedelta(days=anchor.weekday())  # Monday
            end = start + timedelta(days=WEEK_LENGTH_DAYS)
        else:
            raise ValueError("period must be 'weekly' or 'monthly'")

    if start > end:
        raise ValueError('start_date cannot be after end_date')
    return period, start, end


def _in_range(d, start, end):
    return d is not None and start <= d <= end


# ----------------------------------------------------------------------
# SECTION 1 - Sales performance matrix (per salesperson)
# ----------------------------------------------------------------------
SECTION1_ROWS = [
    # key,                label,                          is_currency
    ('physical_visits',   'Physical Visits',              False),
    ('new_prospects',     'New Prospects Identified',     False),
    ('existing_visits',   'Existing Customer Visits',     False),
    ('followups',         'Follow-up Interactions',       False),
    ('samples',           'Samples Delivered / Trials',   False),
    ('quotations_count',  'Quotations Submitted (#)',     False),
    ('quotation_value',   'Quotation Value (UGX)',        True),
    ('orders_count',      'Orders Confirmed (#)',         False),
    ('order_value',       'Order Value Won (UGX)',        True),
    ('cash_collected',    'Cash Collections (UGX)',       True),
    ('overdue',           'Active Overdue Follow-ups',    False),
]


def build_sales_performance(start, end, salesperson_id=None):
    today = timezone.localdate()
    as_of = min(end, today)  # overdue is a "right now" snapshot, never in the future

    people = Salesperson.objects.all()
    if salesperson_id:
        people = people.filter(pk=salesperson_id)

    # Query 1: everything that comes from DailyActivity (single join -> sums are safe)
    act = Q(daily_activities__date__range=(start, end))
    activity_stats = {
        p.id: p for p in people.annotate(
            physical_visits=Count('daily_activities', distinct=True,
                                  filter=act & Q(daily_activities__activity_type='Physical Visit')),
            new_prospects=Count('daily_activities', distinct=True,
                                filter=act & Q(daily_activities__prospect_status__istartswith='New')),
            existing_visits=Count('daily_activities', distinct=True,
                                  filter=act & Q(daily_activities__prospect_status__istartswith='Existing')),
            followups=Count('daily_activities', distinct=True,
                            filter=act & Q(daily_activities__activity_type='Follow-up Interaction')),
            quotations_count=Count('daily_activities', distinct=True,
                                   filter=act & Q(daily_activities__quotation_submitted_value_ugx__gt=0)),
            quotation_value=Sum('daily_activities__quotation_submitted_value_ugx', filter=act),
            cash_collected=Sum('daily_activities__cash_collected_ugx', filter=act),
        )
    }

    # Query 2: everything that comes from CustomerPipeline (separate query so joins never multiply rows)
    won_in_range = Q(pipeline_deals__sales_stage__in=WON_STAGES,
                     pipeline_deals__stage_last_updated__range=(start, end))
    open_deal = ~Q(pipeline_deals__sales_stage__in=CLOSED_STAGES)
    pipeline_stats = {
        p.id: p for p in people.annotate(
            samples=Count('pipeline_deals', distinct=True,
                          filter=Q(pipeline_deals__last_contact_date__range=(start, end))
                          & ~Q(pipeline_deals__sample_trial_status__in=SAMPLE_NOT_STARTED)),
            orders_count=Count('pipeline_deals', distinct=True, filter=won_in_range),
            order_value=Sum('pipeline_deals__actual_order_value_ugx', filter=won_in_range),
            overdue=Count('pipeline_deals', distinct=True,
                          filter=open_deal & Q(pipeline_deals__next_followup_date__lt=as_of)),
        )
    }

    data = {}
    for pid, a in activity_stats.items():
        b = pipeline_stats[pid]
        data[pid] = {
            'name': a.name,
            'is_active': a.is_active,
            'physical_visits': a.physical_visits,
            'new_prospects': a.new_prospects,
            'existing_visits': a.existing_visits,
            'followups': a.followups,
            'samples': b.samples,
            'quotations_count': a.quotations_count,
            'quotation_value': _num(a.quotation_value),
            'orders_count': b.orders_count,
            'order_value': _num(b.order_value),
            'cash_collected': _num(a.cash_collected),
            'overdue': b.overdue,
        }

    # Keep deactivated reps only if they actually have numbers in this period
    keys = [k for k, _, _ in SECTION1_ROWS]
    ordered = sorted(
        (d for d in data.values() if d['is_active'] or any(d[k] for k in keys)),
        key=lambda d: d['name'],
    )

    rows = [{
        'key': key,
        'metric': label,
        'is_currency': is_currency,
        'per_salesperson': {d['name']: d[key] for d in ordered},
        'total_team': sum(d[key] for d in ordered),
    } for key, label, is_currency in SECTION1_ROWS]

    return {'salespersons': [d['name'] for d in ordered], 'rows': rows}


# ----------------------------------------------------------------------
# SECTION 2 - Top active sales opportunities
# ----------------------------------------------------------------------
def build_top_opportunities(start, end, limit=10, salesperson_id=None, touched_only=False):
    today = timezone.localdate()
    qs = (CustomerPipeline.objects.select_related('salesperson')
          .exclude(sales_stage__in=CLOSED_STAGES))
    if salesperson_id:
        qs = qs.filter(salesperson_id=salesperson_id)
    if touched_only:
        qs = qs.filter(
            Q(last_contact_date__range=(start, end))
            | Q(next_followup_date__range=(start, end))
            | Q(stage_last_updated__range=(start, end))
        )

    result = []
    for d in qs.order_by('-estimated_value_ugx')[:limit]:
        result.append({
            'id': d.id,
            'prospect_id': d.prospect_id,
            'customer': d.customer_company,
            'salesperson': d.salesperson.name,
            'product': d.product_service,
            'potential_value_ugx': _num(d.estimated_value_ugx),
            'sales_stage': d.sales_stage,
            'probability_pct': d.probability_pct,
            'next_action': d.next_action,
            'next_followup_date': d.next_followup_date,
            'is_overdue': bool(d.next_followup_date and d.next_followup_date < today),
            'touched_in_period': (_in_range(d.last_contact_date, start, end)
                                  or _in_range(d.next_followup_date, start, end)
                                  or _in_range(d.stage_last_updated, start, end)),
        })
    return result


# ----------------------------------------------------------------------
# SECTION 3 - Competitor / raw material / price intelligence
# ----------------------------------------------------------------------
def build_market_intelligence(start, end, salesperson_id=None):
    qs = (DailyActivity.objects.select_related('salesperson')
          .filter(date__range=(start, end))
          .exclude(market_competitor_intelligence=''))
    if salesperson_id:
        qs = qs.filter(salesperson_id=salesperson_id)

    return [{
        'id': a.id,
        'date': a.date,
        'salesperson': a.salesperson.name,
        'customer': a.customer_company,
        'area': a.area_route_visited or a.specific_location,
        'intelligence': a.market_competitor_intelligence,
        # There is no dedicated "recommended action" column, so the rep's next action is used.
        'recommended_action': a.next_action,
    } for a in qs.order_by('-date', '-id')]


# ----------------------------------------------------------------------
# SECTION 4 - Management / production / sample delays to resolve
# ----------------------------------------------------------------------
def build_management_delays(start, end, salesperson_id=None):
    today = timezone.localdate()
    qs = (DailyActivity.objects.select_related('salesperson')
          .filter(date__range=(start, end))
          .exclude(management_support_needed=''))
    if salesperson_id:
        qs = qs.filter(salesperson_id=salesperson_id)

    result = []
    for a in qs.order_by('required_by_date', '-date'):
        resolved = (a.issue_status or '').strip().lower() in RESOLVED_STATUSES
        result.append({
            'id': a.id,
            'date': a.date,
            'customer': a.customer_company,
            'salesperson': a.salesperson.name,
            'support_required': a.management_support_needed,
            'responsible': a.responsible_person_dept,
            'required_by_date': a.required_by_date,
            'status': a.issue_status,
            'is_past_deadline': bool(a.required_by_date and a.required_by_date < today and not resolved),
        })
    return result


# ----------------------------------------------------------------------
# SECTION 5 - Orders lost & root-cause analysis
# ----------------------------------------------------------------------
def build_orders_lost(start, end, salesperson_id=None):
    qs = (CustomerPipeline.objects.select_related('salesperson')
          .filter(sales_stage__in=LOST_STAGES, stage_last_updated__range=(start, end)))
    if salesperson_id:
        qs = qs.filter(salesperson_id=salesperson_id)

    return [{
        'id': d.id,
        'prospect_id': d.prospect_id,
        'customer': d.customer_company,
        'salesperson': d.salesperson.name,
        'product': d.product_service,
        'potential_value_ugx': _num(d.estimated_value_ugx),
        'reason_lost': d.reason_lost,
        'competitor': d.competitor_won_by,
        'corrective_action': d.corrective_action,
        'lost_on': d.stage_last_updated,
    } for d in qs.order_by('-stage_last_updated', '-id')]


# ----------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------
class ReportAPIView(APIView):
    """Full 5-section report for a weekly, monthly or custom date range."""
    default_period = 'weekly'

    def get(self, request):
        try:
            period, start, end = resolve_period(request.GET, self.default_period)
            salesperson_id = int(request.GET['salesperson']) if request.GET.get('salesperson') else None
            limit = max(1, min(int(request.GET.get('limit', 10)), 100))
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        touched_only = request.GET.get('touched_only', '').lower() in ('1', 'true', 'yes')

        return Response({
            'period': period,
            'start_date': start,
            'end_date': end,
            'generated_at': timezone.now(),
            'salesperson_filter': salesperson_id,
            'sales_performance': build_sales_performance(start, end, salesperson_id),
            'top_opportunities': build_top_opportunities(start, end, limit, salesperson_id, touched_only),
            'market_intelligence': build_market_intelligence(start, end, salesperson_id),
            'management_delays': build_management_delays(start, end, salesperson_id),
            'orders_lost': build_orders_lost(start, end, salesperson_id),
        }, status=status.HTTP_200_OK)


class WeeklyReportAPIView(ReportAPIView):
    default_period = 'weekly'


class MonthlyReportAPIView(ReportAPIView):
    default_period = 'monthly'