from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Prefetch
from .models import Job
import uuid

# DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import JobSerializer

def index(request):
    return render(request, "helloworld/index.html")

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

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def dashboard_view(request):
    if request.method == "POST":
        # Temporarily create job with empty pipeline
        job = Job.objects.create(
            submitted_by=request.user.username,
            step_ids=[1, 2, 3, 4],  # Replace with dynamic IDs if needed
            pipeline_json={},  # placeholder
            status=-2
        )

        # Now construct pipeline with job.id
        pipeline = {
            "job_id": job.id,
            "job_steps": ["pre", "sort", "post", "export"],
            "parameters": {
                "filter_type": "bandpass",
                "sorting_algorithm": "Kilosort",
                "threshold": 5.0
            }
        }

        # Update pipeline_json
        job.pipeline_json = pipeline
        job.save()

        messages.success(request, f"Job {job.id} submitted!")
        return redirect("dashboard")

    return render(request, "helloworld/dashboard.html")

@login_required
def job_history_view(request):
    if request.user.username == "admin":  # Check if the logged-in user is the admin
        jobs = Job.objects.all().order_by('-created_at')  # Fetch all jobs for admin
    else:
        jobs = Job.objects.filter(submitted_by=request.user.username).order_by('-created_at')  # Fetch jobs for the user

    context = {'jobs': jobs}
    return render(request, "helloworld/job_history.html", context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_job(request):
    job = Job.objects.filter(status=-2).order_by('created_at').first()  # Queued only
    if not job:
        return Response(status=204)
    
    # Mark as fetched
    job.status = -1
    job.save()

    return Response(job.pipeline_json)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_job_status(request):
    job_id = request.data.get("job_id")
    status_val = request.data.get("status")
    try:
        job = Job.objects.get(id=job_id)
        job.status = status_val
        job.save()
        return Response({"message": f"Updated job {job_id} to status {status_val}"}, status=201)
    except Job.DoesNotExist:
        return Response({"error": "Invalid job ID"}, status=400)