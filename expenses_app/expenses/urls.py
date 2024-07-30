from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ExpenseViewSet, download_balance_sheet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'expenses', ExpenseViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('download_balance_sheet/', download_balance_sheet, name='download_balance_sheet'),
]
