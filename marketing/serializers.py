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
class SalespersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Salesperson
        fields = '__all__'


class CustomerPipelineSerializer(serializers.ModelSerializer):

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


class DailyActivitySerializer(serializers.ModelSerializer):

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
