from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Prefetch
from .models import Job, Step
import uuid, os
from pathlib import Path
from django.conf import settings

# DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import JobSerializer

# --- Public Pages ---
def index(request):
    return render(request, "helloworld/index.html")

# --- Authentication ---
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

# --- DASHBOARD VIEW ---
# This view handles the dashboard where users can submit jobs
# and view their job history.
# It also handles the form submission for job parameters.
# Constants for file directories
def list_files(directory: str, extension: str):
    """List files in a given directory with a specific extension"""
    dir_path = Path(directory)
    return sorted([str(f) for f in dir_path.glob(f"*.{extension}")])

@login_required
def dashboard_view(request):
    if request.method == "POST":
        # --- 1. Recording fields from dropdown ---
        binfile_path = request.POST.get("binfile")
        probe_path = request.POST.get("probe")
        sampling_rate = float(request.POST.get("sampling_rate"))
        num_channels = int(request.POST.get("num_channels"))

        remove = request.POST.get("remove", "")
        bad_channels = request.POST.get("bad_channels", "")
        gain_to_uV = float(request.POST.get("gain_to_uV", 0.195))
        offset_to_uV = float(request.POST.get("offset_to_uV", 0.0))

        recording = {
            "binfile": binfile_path,
            "sampling rate": sampling_rate,
            "number of channels": num_channels,
            "remove": [int(x) for x in remove.split(",") if x.strip().isdigit()],
            "bad_channels": [int(x) for x in bad_channels.split(",") if x.strip().isdigit()],
            "probe": probe_path,
            "gain_to_uV": gain_to_uV,
            "offset_to_uV": offset_to_uV,
            "location": binfile_path,
        }

        # --- 2. Parse dynamic step parameters ---
        steps = Step.objects.all()
        pipeline_sections = {}
        step_names = []

        for step in steps:
            section_data = {}
            step_names.append(step.step_name)

            for param in step.required_parameters:
                key = f"{step.step_name}_{param}"
                section_data[param] = request.POST.get(key)

            for param in step.optional_parameters:
                key = f"{step.step_name}_{param}"
                value = request.POST.get(key)
                if value:
                    section_data[param] = value

            pipeline_sections[step.step_name] = section_data

        # --- 3. Assemble final pipeline ---
        run_dir = f"{request.user.username}-run-{uuid.uuid4().hex[:6]}"
        pipeline = {
            "recording": recording,
            "running directory": run_dir,
            "rerun": True,
        }
        pipeline.update(pipeline_sections)

        # --- 4. Save job ---
        job = Job.objects.create(
            submitted_by=request.user.username,
            step_ids=[s.id for s in steps],
            pipeline_json=pipeline,
            status=-2
        )

        messages.success(request, f"Job {job.id} submitted successfully!")
        return redirect("dashboard")

    else:
        # On GET → scan file directories
        recording_files = list_files(f"{EXPERIMENTS_DIR}/examples", "dat")
        probe_files = list_files(f"{EXPERIMENTS_DIR}/probes", "json")
        sorter_images = list_files(f"{EXPERIMENTS_DIR}/images", "sif")
        steps = Step.objects.all()

        return render(request, "helloworld/dashboard.html", {
            "steps": steps,
            "recording_files": recording_files,
            "probe_files": probe_files,
            "sorter_images": sorter_images,
        })

# --- JOB HISTORY VIEW ---
@login_required
def job_history_view(request):
    if request.user.username == "admin":  # Check if the logged-in user is the admin
        jobs = Job.objects.all().order_by('-created_at')  # Fetch all jobs for admin
    else:
        jobs = Job.objects.filter(submitted_by=request.user.username).order_by('-created_at')  # Fetch jobs for the user

    context = {'jobs': jobs}
    return render(request, "helloworld/job_history.html", context)

# --- Job API for Worker Node ---
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
    

# --- JOB WIZARD VIEW ---
from formtools.wizard.views import SessionWizardView
from .forms import RecordingForm, StepSelectorForm, PreprocessingForm, SorterForm, PostProcessingForm, ReviewForm
EXPERIMENTS_DIR = settings.EXPERIMENTS_DIR

FORMS = [
    ("recording", RecordingForm),
    ("step_selector", StepSelectorForm),
    ("preprocessing", PreprocessingForm),
    ("sorting", SorterForm),
    ("postprocessing", PostProcessingForm),
    ("review", ReviewForm),
]

TEMPLATES = {
    "recording": "helloworld/job_wizard/recording.html",
    "step_selector": "helloworld/job_wizard/step_selector.html",
    "preprocessing": "helloworld/job_wizard/preprocessing.html",
    "sorting": "helloworld/job_wizard/sorting.html",
    "postprocessing": "helloworld/job_wizard/postprocessing.html",
    "review": "helloworld/job_wizard/review.html",
}

def clean_list_field(value):
    if isinstance(value, str):
        return [int(x) for x in value.split(",") if x.strip().isdigit()]
    elif isinstance(value, list):
        return [int(x) for x in value if str(x).isdigit()]
    return []

class JobWizard(SessionWizardView):
    form_list = FORMS
    template_name = "helloworld/job_wizard/generic.html"  # fallback

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]
    
    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        # Debugging information
        print(f"Current step: {self.steps.current}")
        if form.errors:
            print(f"Form errors on step '{self.steps.current}': {form.errors}")

        if self.steps.current == "step_selector":
            context["available_steps"] = Step.objects.all()
        return context

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        if step == "recording":
            from pathlib import Path
            def get_files(path, ext):
                return [(str(f), f.name) for f in Path(path).glob(f"*.{ext}")]
            
            kwargs['binfile_choices'] = get_files(f"{settings.EXPERIMENTS_DIR}/examples", "dat")
            kwargs['probe_choices'] = get_files(f"{settings.EXPERIMENTS_DIR}/probes", "json")
        elif step in ["preprocessing", "sorting", "postprocessing"]:
            kwargs['step_model_data'] = Step.objects.all()

        return kwargs

    def done(self, form_list, **kwargs):
        print("Done method executed!")
        form_data = self.get_all_cleaned_data()

        # Retrieve bad_channels from request manually
        binfile_path = form_data.get("binfile")
        probe_path = form_data.get("probe")
        # Retrieve bad_channels from request manually
        bad_channels_str = form_data.get("bad_channels_hidden", "")
        bad_channels = [int(x) for x in bad_channels_str.split(",") if x.strip().isdigit()]
        print(f"Bad channels: {bad_channels}")  # Debugging

        # --- Recording Block ---
        recording = {
        "binfile": binfile_path,
        "probe": probe_path,
        "sampling rate": float(form_data.get("sampling_rate")),
        "number of channels": int(form_data.get("num_channels")),
        "remove": [int(x) for x in form_data.get("remove", "").split(",") if x.strip().isdigit()],
        "bad_channels": bad_channels,
        "gain_to_uV": float(form_data["gain_to_uV"]) if form_data["gain_to_uV"] is not None else 0.195,
        "offset_to_uV": float(form_data["offset_to_uV"]) if form_data["offset_to_uV"] is not None else 0.0,
        "location": binfile_path,
    }

        # --- Step Selector Booleans ---
        enabled_steps = Step.objects.all().filter(step_name__in=[
            step.step_name for step in Step.objects.all()
            if f"run_{step.step_name}" in self.request.POST
        ])        

        # --- Collect pipeline config blocks ---
        pipeline = {
            "recording": recording,
            "running directory": f"{self.request.user.username}-run-{uuid.uuid4().hex[:6]}",
            "rerun": True,
        }

        for step in enabled_steps:
            step_name = step.step_name

            # --- Preprocessing Section ---
            if step_name == "preprocessing":
                preprocessing = {"methods": []}
                for param in step.required_parameters + step.optional_parameters:
                    val = form_data.get(param)
                    if val:
                        preprocessing["methods"].append(param)
                        preprocessing[param] = {"value": val}
                pipeline["preprocessing"] = preprocessing

            # --- Sorting Section ---
            elif step_name == "sorter":
                sorter_name = form_data["sorter_name"]
                sorter = {
                    "name": sorter_name,
                    sorter_name: {
                        k: form_data.get(k) for k in step.optional_parameters if form_data.get(k)
                    }
                }
                pipeline["sorter"] = sorter
                pipeline["sorters"] = {sorter_name: f"images/{sorter_name}.sif"}

            # --- Postprocessing Section ---
            elif step_name in ["analyzer", "report", "export2matlab"]:
                config = {}
                for param in step.required_parameters + step.optional_parameters:
                    val = form_data.get(f"{step_name}_{param}")
                    if val:
                        config[param] = val
                pipeline[step_name] = config

        # --- Save Final Job ---
        job = Job.objects.create(
            submitted_by=self.request.user.username,
            step_ids=[],
            pipeline_json=pipeline,
            status=-2
        )

        messages.success(self.request, f"Job {job.id} submitted successfully!")
        return redirect("dashboard")