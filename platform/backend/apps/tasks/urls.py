# -*- coding: utf-8 -*-
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestTaskViewSet

router = DefaultRouter()
router.register(r'tasks', TestTaskViewSet, basename='task')

urlpatterns = [
    path('', include(router.urls)),
]
