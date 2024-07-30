from rest_framework import serializers
from .models import User, Expense, ExpenseSplit

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'mobile_number']

class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'amount', 'percentage']

class ExpenseSerializer(serializers.ModelSerializer):
    splits = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = ['id', 'description', 'amount', 'created_at', 'split_method', 'splits']

    def get_splits(self, obj):
        if obj.split_method == 'P':
            # Calculate the amounts based on percentage splits:
            splits = obj.splits.all()
            total_amount = obj.amount
            result = []
            for split in splits:
                if split.percentage is not None:
                    amount = float(total_amount) * float(split.percentage / 100)
                    result.append({
                        'user': split.user.id,
                        'amount': round(amount, 2),
                        'percentage': split.percentage
                    })
            return result
        else:
            # Handle other split methods:
            return ExpenseSplitSerializer(obj.splits.all(), many=True).data