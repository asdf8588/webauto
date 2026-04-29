# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import AllureReport, TraceFile


@admin.register(AllureReport)
class AllureReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'task', 'total', 'passed', 'pass_rate', 
                   'duration', 'created_at']
    readonly_fields = ['created_at']


@admin.register(TraceFile)
class TraceFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'filesize_display', 'test_case', 
                   'task', 'created_at']
    search_fields = ['filename', 'test_case']
