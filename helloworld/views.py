from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Prefetch
from .models import Job, JobStep, JobStatus
import uuid

# DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import JobSerializer, JobStatusSerializer

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
        job_id = str(uuid.uuid4())[:8]

        pipeline = {
            "job_id": job_id,
            "job_steps": ["pre", "sort", "post", "export"],
            "parameters": {
                "filter_type": "bandpass",
                "sorting_algorithm": "Kilosort",
                "threshold": 5.0
            }
        }

        job = Job.objects.create(
            job_id=job_id,
            submitted_by=request.user,
            description="Auto-submitted from dashboard",
            pipeline_json=pipeline
        )

        for step in pipeline["job_steps"]:
            step_obj = JobStep.objects.create(job=job, step_name=step)
            JobStatus.objects.update_or_create(
                step=step_obj,
                defaults={"status": "pending", "message": "Queued for processing."}
            )

        messages.success(request, f"Job {job_id} submitted!")
        return redirect("dashboard")

    return render(request, "helloworld/dashboard.html")

@login_required
def job_history_view(request):
    jobs = Job.objects.filter(submitted_by=request.user).prefetch_related(
        Prefetch('steps', queryset=JobStep.objects.select_related('status'))
    ).order_by('-created_at')

    context = {'jobs': jobs}
    return render(request, "helloworld/job_history.html", context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_job(request):
    job = Job.objects.filter(steps__status__status="pending").first()
    if not job:
        return Response(status=204)
    return Response(job.pipeline_json)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_job_status(request):
    job_id = request.data.get("job_id")
    step_name = request.data.get("step_name")
    status_val = request.data.get("status")
    message = request.data.get("message", "")

    try:
        job = Job.objects.get(job_id=job_id)
        step = JobStep.objects.get(job=job, step_name=step_name)
        JobStatus.objects.update_or_create(
            step=step,
            defaults={"status": status_val, "message": message}
        )
        return Response({"message": "Status updated."}, status=201)
    except (Job.DoesNotExist, JobStep.DoesNotExist):
        return Response({"error": "Invalid job_id or step_name."}, status=400)
