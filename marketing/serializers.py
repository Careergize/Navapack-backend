from rest_framework import serializers

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

from auditlog.models import LogEntry
from .permissions import is_management


class SalesRecordSerializerMixin:
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request is not None and not is_management(request.user):
            fields['salesperson'].read_only = True
            fields[self.record_date_field].read_only = True
        return fields


class SalespersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Salesperson
        fields = '__all__'
        read_only_fields = ('user',)


class CustomerPipelineSerializer(SalesRecordSerializerMixin, serializers.ModelSerializer):
    record_date_field = 'date_added'
    estimated_price_ugx = serializers.DecimalField(
        source='estimated_price', max_digits=15, decimal_places=2, required=False,
    )

    def to_internal_value(self, data):
        if 'estimated_price' in data and 'estimated_price_ugx' in data:
            price = self.fields['estimated_price'].run_validation(data['estimated_price'])
            alias = self.fields['estimated_price_ugx'].run_validation(data['estimated_price_ugx'])
            if price != alias:
                raise serializers.ValidationError({
                    'estimated_price_ugx': 'Must match estimated_price when both fields are supplied.',
                })
        return super().to_internal_value(data)

    salesperson_detail = SalespersonSerializer(
        source='salesperson',
        read_only=True
    )

    salesperson = serializers.PrimaryKeyRelatedField(
        queryset=Salesperson.objects.all()
    )

    class Meta:
        model = CustomerPipeline
        fields = '__all__'


class DailyActivitySerializer(SalesRecordSerializerMixin, serializers.ModelSerializer):
    record_date_field = 'date'

    salesperson_detail = SalespersonSerializer(
        source='salesperson',
        read_only=True
    )

    salesperson = serializers.PrimaryKeyRelatedField(
        queryset=Salesperson.objects.all()
    )

    class Meta:
        model = DailyActivity
        fields = '__all__'


class DropdownListsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DropdownLists
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name')


class ProductServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductService
        fields = '__all__'


class SalesStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SalesStage
        fields = '__all__'


class ActivityTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActivityType
        fields = '__all__'


class UnitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Unit
        fields = '__all__'

from rest_framework import serializers
from auditlog.models import LogEntry


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(
        source='actor.username',
        read_only=True
    )

    class Meta:
        model = LogEntry
        fields = [
            'id',
            'action',
            'user',
            'timestamp',
            'object_id',
            'object_repr',
            'changes',
        ]


from .models import FollowupNotification


class FollowupNotificationSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source='customer_pipeline.customer_company', read_only=True)

    class Meta:
        model = FollowupNotification
        fields = '__all__'
