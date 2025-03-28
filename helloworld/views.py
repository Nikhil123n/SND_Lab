from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.
def index(request):
    return render(request, "helloworld/index.html")

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.GET.get('next'):
        messages.info(request, "Please log in to continue.")  # Session timeout or unauthorized
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Check if username and password are provided
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, "helloworld/login.html")
        
        user = authenticate(request, username=username, password=password)
        
        # Check if the user is active
        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirect to the next page after login
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "helloworld/login.html")

@login_required
def dashboard_view(request):
    return render(request, "helloworld/dashboard.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

# This view handles the submission of a pipeline job.
# It generates a unique job ID, prepares the pipeline data, and submits it to a Celery task.
from .tasks import submit_pipeline_job
import uuid
@login_required
def dashboard_view(request):
    if request.method == "POST":
        job_id = str(uuid.uuid4())[:8]
        pipeline_data = {
            "job_id": job_id,
            "job_steps": ["pre", "sort", "post", "export"],
            "parameters": {
                "filter_type": "bandpass",
                "sorting_algorithm": "Kilosort",
                "threshold": 5.0
            }
        }

        submit_pipeline_job.delay(job_id, pipeline_data)
        messages.success(request, f"Job {job_id} submitted!")
        return redirect("dashboard")

    return render(request, "helloworld/dashboard.html")
