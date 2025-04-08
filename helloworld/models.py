# helloworld/models.py
from django.db import models
from django.contrib.auth.models import User

# Job Status Choices
STATUS_CHOICES = [
        (-2, "Queued"),
        (-1, "Fetched"),
        (99, "Completed"),
        (-99, "Failed")
        # Step index values (0, 1, 2, ...) will be used dynamically in code
]

class Job(models.Model):
    submitted_by = models.CharField(max_length=150)  # Store the username directly
    step_ids = models.JSONField(default=list)  # list of integers referring to Step ids
    pipeline_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.SmallIntegerField(default=-2, choices=STATUS_CHOICES)

    def __str__(self):
        return f"Job {self.id} by {self.submitted_by}"

class Step(models.Model):
    step_name = models.CharField(max_length=50, unique=True)
    required_parameters = models.JSONField(default=list)
    optional_parameters = models.JSONField(default=list)

    def __str__(self):
        return self.step_name
    
# class JobStep(models.Model):
#     STEP_CHOICES = [
#         ("pre", "Preprocessing"),
#         ("sort", "Sorting"),
#         ("post", "Postprocessing"),
#         ("export", "Exporting"),
#     ]

#     job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='steps')
#     step_name = models.CharField(max_length=20, choices=STEP_CHOICES)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.job.job_id} - {self.step_name}"

# class JobStatus(models.Model):
#     STATUS_CHOICES = [
#         ("pending", "Pending"),
#         ("running", "Running"),
#         ("complete", "Complete"),
#         ("failed", "Failed"),
#     ]

#     step = models.OneToOneField(JobStep, on_delete=models.CASCADE, related_name='status')
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES)
#     message = models.TextField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.step.step_name} - {self.status}"
