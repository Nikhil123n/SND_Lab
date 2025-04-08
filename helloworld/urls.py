from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import login_view, dashboard_view, logout_view
from . import views
from .views import get_next_job, submit_job_status, job_history_view

urlpatterns = [
    # Django admin
    path("", views.index, name="index"),    

    # Django auth views
    path("login/", login_view, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"), 
    path('logout/', logout_view, name='logout'),    
    path('job-history/', job_history_view, name='job-history'),

    # API endpoints
    path('api/next-job/', get_next_job, name='api-next-job'),
    path('api/status/', submit_job_status, name='api-submit-status'),
]