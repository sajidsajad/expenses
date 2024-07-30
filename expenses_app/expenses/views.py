from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import User, Expense, ExpenseSplit
from .serializers import UserSerializer, ExpenseSerializer
from django.http import HttpResponse

import csv
from io import StringIO


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer




class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer


    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['description']

    def create(self, request, *args, **kwargs):
        data = request.data
        participants = data.pop('participants', [])
        
        try:
            # Ensure amount is a float
            data['amount'] = float(data['amount'])
        except (ValueError, TypeError):
            return Response({"detail": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
        
        expense = Expense.objects.create(**data)

        if expense.split_method == 'E':
            # Equal split logic
            num_participants = len(participants)
            if num_participants == 0:
                return Response({"detail": "At least one participant is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            amount_per_user = round(expense.amount / num_participants, 2)
            for participant in participants:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=participant['user'],
                    amount=amount_per_user,
                    percentage=None
                )
        elif expense.split_method == 'X':
            # Exact amounts logic
            for participant in participants:
                try:
                    participant_amount = float(participant['amount'])
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid amount format in participants"}, status=status.HTTP_400_BAD_REQUEST)
                
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=participant['user'],
                    amount=participant_amount,
                    percentage=None
                )
        elif expense.split_method == 'P':
            # Percentage logic
            total_percentage = 0
            for participant in participants:
                try:
                    percentage = float(participant['percentage'])
                except (ValueError, TypeError):
                    return Response({"detail": "Invalid percentage format in participants"}, status=status.HTTP_400_BAD_REQUEST)
                
                total_percentage += percentage
            
            if total_percentage != 100:
                return Response({"detail": "Percentages must add up to 100%"}, status=status.HTTP_400_BAD_REQUEST)
            
            for participant in participants:
                percentage = float(participant['percentage'])
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=participant['user'],
                    amount=None,
                    percentage=percentage
                )

        serializer = self.get_serializer(expense)
        # serializer = self.retrieve(self, request, *args, **kwargs)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        expense = self.get_object()
        serializer = self.get_serializer(expense)
        return Response(serializer.data)

    # def download_balance_sheet(self, request, *args, **kwargs):
        expenses = Expense.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=balance_sheet.csv'

        writer = csv.writer(response)
        writer.writerow(['Expense Description', 'User Name', 'Amount', 'Percentage'])
        for expense in expenses:
            for split in expense.expensesplit_set.all():
                writer.writerow([
                    expense.description,
                    split.user.name,
                    split.amount if split.amount else '',
                    split.percentage if split.percentage else ''
                ])
        return response

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get('user')
        if user_id is not None:
            queryset = queryset.filter(splits__user_id=user_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

def generate_balance_sheet(expenses):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Expense ID', 'Description', 'Amount', 'User', 'Split Method', 'Amount Owed', 'Percentage'])

    for expense in expenses:
        total_amount = Decimal(expense.amount)
        splits = expense.splits.all()
        for split in splits:
            user_id = split.user.id
            percentage = Decimal(split.percentage) if split.percentage is not None else Decimal('0.0')
            amount = Decimal(split.amount) if expense.split_method != 'P' else total_amount * (percentage / Decimal('100.0'))
            
            writer.writerow([
                expense.id,
                expense.description,
                total_amount,
                user_id,
                expense.split_method,
                round(amount, 2),
                percentage if expense.split_method == 'P' else ''
            ])

    output.seek(0)
    return output.getvalue()

def download_balance_sheet(request):
    expenses = Expense.objects.all()
    csv_data = generate_balance_sheet(expenses)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="balance_sheet.csv"'
    return response