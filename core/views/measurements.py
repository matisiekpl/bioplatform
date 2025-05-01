from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.core.files import File
import os
import shutil
from django.conf import settings
from core.models import Experiment, Measurement, Membership
from core.forms import MeasurementForm, ImageAnalysisForm
from core.utils import extract_cells
from .mixins import TeamRoleRequiredMixin


class MeasurementListView(LoginRequiredMixin, ListView):
    model = Measurement
    template_name = 'core/measurements/measurement_list.html'
    context_object_name = 'measurements'

    def get_queryset(self):
        experiment_id = self.kwargs.get('experiment_id')
        measurement_type = self.request.GET.get('type')
        
        queryset = Measurement.objects.filter(experiment_id=experiment_id).order_by('-timestamp')
        
        if measurement_type:
            queryset = queryset.filter(type=measurement_type)
        elif Measurement.objects.filter(experiment_id=experiment_id).exists():
            # Default to first measurement type if no type is specified and measurements exist
            first_measurement = Measurement.objects.filter(experiment_id=experiment_id).first()
            if first_measurement:
                queryset = queryset.filter(type=first_measurement.type)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = Experiment.objects.get(id=self.kwargs.get('experiment_id'))
        context['experiment'] = experiment
        context['team'] = experiment.team
        
        # Add user's role to context for template permission checks
        membership = Membership.objects.filter(
            user=self.request.user,
            team_id=experiment.team_id
        ).first()
        context['user_role'] = membership.role if membership else None
        
        # Add measurement types for the selector
        context['measurement_types'] = Measurement.Type.choices
        context['selected_type'] = self.request.GET.get('type', '')
        
        # If no type is selected but measurements exist, select the first type
        if not context['selected_type'] and self.get_queryset().exists():
            context['selected_type'] = self.get_queryset().first().type
            
        return context


class MeasurementCreateView(LoginRequiredMixin, TeamRoleRequiredMixin, CreateView):
    model = Measurement
    form_class = MeasurementForm
    template_name = 'core/measurements/measurement_form.html'
    required_role = Membership.Role.EDITOR

    def form_valid(self, form):
        form.instance.experiment_id = self.kwargs.get('experiment_id')
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        experiment = Experiment.objects.get(id=self.kwargs.get('experiment_id'))
        context['experiment'] = experiment
        context['team'] = experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.kwargs.get('experiment_id')})


class MeasurementUpdateView(LoginRequiredMixin, TeamRoleRequiredMixin, UpdateView):
    model = Measurement
    form_class = MeasurementForm
    template_name = 'core/measurements/measurement_form.html'
    required_role = Membership.Role.EDITOR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiment'] = self.object.experiment
        context['team'] = self.object.experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.object.experiment_id})


class MeasurementDeleteView(LoginRequiredMixin, TeamRoleRequiredMixin, DeleteView):
    model = Measurement
    template_name = 'core/measurements/measurement_confirm_delete.html'
    required_role = Membership.Role.EDITOR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['experiment'] = self.object.experiment
        context['team'] = self.object.experiment.team
        return context

    def get_success_url(self):
        return reverse('measurement_list', kwargs={'experiment_id': self.object.experiment_id})


@login_required
def analyze_image_form(request, experiment_id):
    """View for uploading an image for cell analysis"""
    experiment = get_object_or_404(Experiment, id=experiment_id)
    
    # Check if user has permission to create measurements
    membership = Membership.objects.filter(
        user=request.user,
        team=experiment.team
    ).first()
    
    if not membership or membership.role not in [Membership.Role.EDITOR, Membership.Role.ADMIN]:
        messages.error(request, "You don't have permission to add measurements to this experiment.")
        return redirect('experiment_list', team_id=experiment.team_id)
    
    if request.method == 'POST':
        form = ImageAnalysisForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            # Store image temporarily in session
            request.session['analysis_image_path'] = image.name
            
            # Upload and analyze the image
            cell_count, original_img, contours_img = extract_cells(image)
            
            # Store results in session for the results page
            request.session['cell_count'] = cell_count
            request.session['original_img'] = original_img
            request.session['contours_img'] = contours_img
            request.session['experiment_id'] = experiment_id
            
            return redirect('analyze_image_results')
    else:
        form = ImageAnalysisForm()
    
    return render(request, 'core/measurements/analyze_image_form.html', {
        'form': form,
        'experiment': experiment,
        'team': experiment.team
    })


@login_required
def analyze_image_results(request):
    """View for displaying analysis results and creating a measurement"""
    # Get data from session
    cell_count = request.session.get('cell_count')
    original_img = request.session.get('original_img')
    contours_img = request.session.get('contours_img')
    experiment_id = request.session.get('experiment_id')
    
    if not all([cell_count is not None, original_img, contours_img, experiment_id]):
        messages.error(request, "Analysis data not found. Please try again.")
        return redirect('measurement_list', experiment_id=experiment_id)
    
    experiment = get_object_or_404(Experiment, id=experiment_id)
    
    if request.method == 'POST':
        # Create new measurement with the analyzed data
        if 'save' in request.POST:
            timestamp = timezone.now()
            
            # Use the corrected count if provided
            try:
                corrected_count = int(request.POST.get('corrected_count', cell_count))
                if corrected_count < 0:
                    corrected_count = 0
            except (ValueError, TypeError):
                corrected_count = cell_count
                
            # Fix for handling the image path - need to create a File object from the path
            
            # Path to the actual file on disk
            image_path = os.path.join(settings.MEDIA_ROOT, original_img)
            
            measurement = Measurement(
                experiment=experiment,
                type=Measurement.Type.CELL_COUNT,
                value=corrected_count,  # Use the corrected value
                timestamp=timestamp,
                created_by=request.user
            )
            
            # Save measurement first to get an ID
            measurement.save()
            
            # Now handle image - copy file to the measurement_images directory
            target_dir = os.path.join(settings.MEDIA_ROOT, 'measurement_images')
            os.makedirs(target_dir, exist_ok=True)
            
            # Extract filename from path and create a new unique name
            image_filename = os.path.basename(original_img)
            new_filename = f"measurement_{measurement.id}_{image_filename}"
            target_path = os.path.join(target_dir, new_filename)
            
            # Copy the file
            shutil.copy(image_path, target_path)
            
            # Set the image field to the relative path that Django expects
            measurement.image = f"measurement_images/{new_filename}"
            measurement.save()
            
            # Clear session data
            for key in ['cell_count', 'original_img', 'contours_img', 'experiment_id', 'analysis_image_path']:
                if key in request.session:
                    del request.session[key]
            
            # Add success message showing if the count was corrected        
            if corrected_count != cell_count:
                messages.success(request, f"Successfully saved measurement with manually corrected count of {corrected_count} cells (originally detected: {cell_count}).")
            else:
                messages.success(request, f"Successfully saved measurement with {corrected_count} cells.")
                
            return redirect('measurement_list', experiment_id=experiment_id)
        else:
            # User cancelled, clear session data
            for key in ['cell_count', 'original_img', 'contours_img', 'experiment_id', 'analysis_image_path']:
                if key in request.session:
                    del request.session[key]
            
            return redirect('measurement_list', experiment_id=experiment_id)
    
    return render(request, 'core/measurements/analyze_image_results.html', {
        'cell_count': cell_count,
        'original_img': original_img,
        'contours_img': contours_img,
        'experiment': experiment,
        'team': experiment.team
    }) 