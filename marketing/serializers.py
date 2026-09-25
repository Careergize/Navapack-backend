from rest_framework import serializers

from .models import (
    Salesperson,
    CustomerPipeline,
    DailyActivity,
    DropdownLists,
)


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

