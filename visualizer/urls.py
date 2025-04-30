print("--- !!! EXECUTING VISUALIZER URLS.PY !!! ---")
# visualizer/urls.py

from django.urls import path
from . import views

app_name = 'visualizer'
urlpatterns = [
    path('', views.upload_file_view, name='upload_dataset'), # Map root to upload view
    # Placeholder for the next view
    #path('convert-to-xlsx/', views.convert_to_xlsx_view, name='convert_to_xlsx'),
    path('visualizer/', views.visualizer_interface, name='visualizer_interface'), # Map to visualizer view

    path('chart', views.chart_only_view, name='chart_only')
]