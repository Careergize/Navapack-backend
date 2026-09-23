from rest_framework import serializers
from .models import Salesperson, CustomerPipeline, DailyActivity, DropdownLists


class SalespersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salesperson
        fields = '__all__'


class CustomerPipelineSerializer(serializers.ModelSerializer):
    # Returns nested salesperson object for GET
    salesperson_detail = SalespersonSerializer(
        source='salesperson',
        read_only=True
    )

    # Accepts salesperson ID for POST/PUT
    salesperson = serializers.PrimaryKeyRelatedField(
        queryset=Salesperson.objects.all()
    )

    class Meta:
        model = CustomerPipeline
        fields = '__all__'


class DailyActivitySerializer(serializers.ModelSerializer):
    # Returns nested salesperson object for GET
    salesperson_detail = SalespersonSerializer(
        source='salesperson',
        read_only=True
    )

    # Accepts salesperson ID for POST/PUT
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