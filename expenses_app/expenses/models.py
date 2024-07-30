from django.db import models
from django.core.exceptions import ValidationError

class User(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name

class Expense(models.Model):
    SPLIT_METHODS = (
        ('E', 'Equal'),
        ('X', 'Exact'),
        ('P', 'Percentage'),
    )

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    split_method = models.CharField(max_length=1, choices=SPLIT_METHODS)
    participants = models.ManyToManyField(User, through='ExpenseSplit')

    def __str__(self):
        return self.description

class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, related_name='splits', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def clean(self):
        if self.expense.split_method == 'P':
            # Validate that percentages add up to 100%
            total_percentage = self.expense.expensesplit_set.aggregate(total=models.Sum('percentage'))['total'] or 0
            if total_percentage != 100:
                raise ValidationError('Percentages must add up to 100%')
        if self.expense.split_method == 'X' and self.amount is None:
            raise ValidationError('Exact amount is required for exact split method')
        if self.expense.split_method == 'P' and self.percentage is None:
            raise ValidationError('Percentage is required for percentage split method')

    def __str__(self):
        return f"{self.user.name} owes {self.amount if self.amount else self.percentage}% of {self.expense.description}"
