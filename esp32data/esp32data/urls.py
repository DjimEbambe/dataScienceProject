"""
URL configuration for esp32data project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from datareceiver.views import receive_data
from datareceiver.views import home

from datareceiver.views import export_to_csv
from datareceiver.views import export_to_excel
from datareceiver.views import export_to_json


urlpatterns = [
    path('', home, name='home'),
    path('data/', receive_data,  name='receive_data'),
    path('local/<str:local>/', home, name='local_data'),
    path('export/csv/', export_to_csv, name='export_csv'),
    path('export/csv/<str:local>/', export_to_csv, name='export_csv_local'),
    path('export/excel/', export_to_excel, name='export_excel'),
    path('export/excel/<str:local>/', export_to_excel, name='export_excel_local'),
    path('export/json/', export_to_json, name='export_json'),
    path('export/json/<str:local>/', export_to_json, name='export_json_local'),
    #path('bokeh/', include('datareceiver.urls'))
]
