from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Measurement
from django.http import JsonResponse, HttpResponse
import json
import csv
from django.http import HttpResponse
from openpyxl import Workbook

from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from bokeh.plotting import figure, output_file, show
import numpy as np


from bokeh.embed import components

# Helpert H Data filter
def get_filtered_measurements(request):
    measurements_query = Measurement.objects.all().order_by('-timestamp')
    
    # Filtering by local if selected
    local = request.GET.get('local')
    if local and local != 'all':
        measurements_query = measurements_query.filter(local=local)

    # Date filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start_datetime = parse_datetime(f"{start_date}T00:00:00Z")
        end_datetime = parse_datetime(f"{end_date}T23:59:59Z")
        measurements_query = measurements_query.filter(timestamp__range=(start_datetime, end_datetime))
    
    return measurements_query


def forecast_feature(measurements, feature):
    df = pd.DataFrame(list(measurements.values('timestamp', feature)))
    df.set_index('timestamp', inplace=True)
    df = df.asfreq('H').fillna(method='ffill')  # Ensuring frequency and filling missing values

    # Prepare data for machine learning models
    X = (df.index.values - np.datetime64('1970-01-01T00:00:00Z')).astype(float) / 1e9  # Convert to seconds
    X = X.reshape(-1, 1)
    y = df[feature].values

    # Fit ARIMA model
    model_arima = ARIMA(y, order=(1, 1, 1)).fit()
    
    # Fit Linear Regression and Random Forest models
    model_lr = LinearRegression().fit(X, y)
    model_rf = RandomForestRegressor().fit(X, y)

    # Prepare Bokeh plot
    p = figure(title=f"{feature.capitalize()} Forecast", x_axis_type="datetime")
    p.line(df.index, y, legend_label="Actual", line_width=2)
    p.line(df.index, model_arima.fittedvalues, legend_label="ARIMA", color="orange", line_dash="dashed")
    p.line(df.index, model_lr.predict(X), legend_label="Linear Regression", color="purple", line_dash="dotted")
    p.line(df.index, model_rf.predict(X), legend_label="Random Forest", color="brown", line_dash="dotdash")

    # Embed plot components
    script, div = components(p)
    return script, div

def render_graph(measurements, feature):
    df = pd.DataFrame(list(measurements.values('timestamp', feature)))
    df.set_index('timestamp', inplace=True)
    df = df.asfreq('H').fillna(method='ffill')  # Ensuring frequency and filling missing values

    p = figure(title=f"{feature.capitalize()} Graph", x_axis_type="datetime")
    p.line(df.index, df[feature], legend_label="Actual", line_width=2)

    script, div = components(p)
    return script, div



@csrf_exempt
def receive_data(request):
    if request.method == 'POST':
        try:
            # Convert all values to their expected types (float for simplicity here)
            local= str(request.POST.get('local', ""))
            humidity = float(request.POST.get('humidity', 0))
            temperature = float(request.POST.get('temperature', 0))
            current = float(request.POST.get('current', 0))
            voltage = float(request.POST.get('voltage', 0))
            energy = float(request.POST.get('energy', 0))
        except ValueError:
            # Handle cases where conversion fails
            return HttpResponse("Invalid input data, expected numerical values", status=400)

        # Create a new Measurement instance
        Measurement.objects.create(
            local=local,
            humidity=humidity,
            temperature=temperature,
            current=current,
            voltage=voltage,
            energy=energy
        )
        # Return a success message
        return HttpResponse("Data received", status=201)
    else:
        return HttpResponse("Send data via POST", status=400)



def home(request):
    measurements = get_filtered_measurements(request)
    context = {
        'page_obj': Paginator(measurements, 10).get_page(request.GET.get('page')),
        'locations': Measurement.objects.values_list('local', flat=True).distinct(),
        'selected_local': request.GET.get('local', 'all')
    }

    # Check if the query parameter 'get' is set to 1
    render_ml_models = request.GET.get('get') == '1'

    # Render machine learning models only if 'render_ml_models' is True
    if render_ml_models:
        for feature in ['humidity', 'temperature', 'energy']:
            context[f'{feature}_forecast_script'], context[f'{feature}_forecast_div'] = forecast_feature(measurements, feature)

    # By default, render only the graph without machine learning models
    else:
        for feature in ['humidity', 'temperature', 'energy']:
            context[f'{feature}_graph_script'], context[f'{feature}_graph_div'] = render_graph(measurements, feature)

    return render(request, 'index.html', context)



def export_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="measurements.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Temperature', 'Humidity', 'Current', 'Voltage', 'Energy', 'Local'])

    measurements = get_filtered_measurements(request).values_list('timestamp', 'temperature', 'humidity', 'current', 'voltage', 'energy', 'local')
    for measurement in measurements:
        writer.writerow(measurement)

    return response


def export_to_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="measurements.xlsx"'

    wb = Workbook()
    ws = wb.active
    ws.append(['Timestamp', 'Temperature', 'Humidity', 'Current', 'Voltage', 'Energy', 'Local'])

    for measurement in get_filtered_measurements(request):
        ws.append([measurement.timestamp, measurement.temperature, measurement.humidity, measurement.current, measurement.voltage, measurement.energy, measurement.local])

    wb.save(response)
    return response

def export_to_json(request):
    data = list(get_filtered_measurements(request).values())
    return JsonResponse(data, safe=False)

