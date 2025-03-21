from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import login_view, dashboard_view, logout_view
from . import views

urlpatterns = [
    path("", views.index, name="index"),    
    path("login/", login_view, name="login"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path('logout/', logout_view, name='logout'),

]