from django import forms
from .models import Step
from django.conf import settings

# Step 1 – No fields needed since you're manually rendering everything
from django import forms

class RecordingForm(forms.Form):
    binfile = forms.ChoiceField(
        label="Select Recording File (.dat)",
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_binfile'
        }),
        required=True
    )

    probe = forms.ChoiceField(
        label="Select Probe File (.json)",
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_probe'
        }),
        required=True
    )

    sampling_rate = forms.FloatField(
        label="Sampling Rate (Hz)",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'id': 'id_sampling_rate'
        })
    )

    num_channels = forms.IntegerField(
        label="Number of Channels",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_num_channels'
        })
    )

    remove = forms.CharField(
        label="Remove Channels (comma-separated)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_remove',
            'placeholder': 'e.g., 256,257,258'
        })
    )

    gain_to_uV = forms.FloatField(
        label="Gain to uV",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'id': 'id_gain_to_uV',
            'placeholder': 'Default: 0.195'
        })
    )

    offset_to_uV = forms.FloatField(
        label="Offset to uV",
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': 'any',
            'id': 'id_offset_to_uV',
            'placeholder': 'Default: 0.0'
        })
    )

    bad_channels_hidden = forms.CharField(
        label="Bad Channels (Hidden)",
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'bad_channels_hidden'
        })
    )

    def __init__(self, *args, **kwargs):
        binfile_choices = kwargs.pop('binfile_choices', [])
        probe_choices = kwargs.pop('probe_choices', [])
        super().__init__(*args, **kwargs)

        self.fields['binfile'].choices = binfile_choices
        self.fields['probe'].choices = probe_choices

# Step 2 – Just a placeholder for wizard navigation
class StepSelectorForm(forms.Form):
    pass

# Step 3 – Dynamically built from Step table
class PreprocessingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        step_data = kwargs.pop('step_model_data', None)
        super().__init__(*args, **kwargs)

        preproc_step = step_data.filter(step_name="preprocessing").first()
        if preproc_step:
            for param in preproc_step.required_parameters:
                self.fields[param] = forms.CharField(
                    label=f"{param.title()} (Required)",
                    required=True,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )
            for param in preproc_step.optional_parameters:
                self.fields[param] = forms.CharField(
                    label=f"{param.title()} (Optional)",
                    required=False,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )

# Step 4 – Choose sorter, then parameters
class SorterForm(forms.Form):
    sorter_name = forms.ChoiceField(
        label="Select Sorter",
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        step_data = kwargs.pop('step_model_data', None)
        super().__init__(*args, **kwargs)

        sorter_step = step_data.filter(step_name="sorter").first()
        if sorter_step:
            self.fields['sorter_name'].choices = [(s, s) for s in sorter_step.required_parameters]

            for param in sorter_step.optional_parameters:
                self.fields[param] = forms.CharField(
                    label=f"{param.title()} (Optional)",
                    required=False,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )

# Step 5 – Build fields from analyzer, report, export2matlab steps
class PostProcessingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        step_data = kwargs.pop('step_model_data', None)
        super().__init__(*args, **kwargs)

        post_steps = ["analyzer", "report", "export2matlab"]
        for step_name in post_steps:
            step = step_data.filter(step_name=step_name).first()
            if step:
                for param in step.required_parameters:
                    self.fields[f"{step_name}_{param}"] = forms.CharField(
                        label=f"{step_name.title()}: {param.title()} (Required)",
                        required=True,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                for param in step.optional_parameters:
                    self.fields[f"{step_name}_{param}"] = forms.CharField(
                        label=f"{step_name.title()}: {param.title()} (Optional)",
                        required=False,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )

# Step 6 – Final confirmation checkbox
class ReviewForm(forms.Form):
    confirm = forms.BooleanField(
        label="I confirm this configuration is correct.",
        required=True
    )