from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ResumeUploadForm
from django.contrib import messages
from .models import Resume, parsed_data
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# Create your views here.
@login_required
def upload_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            resume = form.save()
            messages.success(request,f'Your Resume uploaded successfully.')

            return redirect('/')
    else:
        form = ResumeUploadForm(user=request.user)
    return render(request, 'resumes/upload_resume.html', {'form':form})

@login_required
def resumes_list(request):
    resume = Resume.objects.filter(user_id=request.user).exclude(status='7')

    return render(request, 'resumes/resumes_list.html', {'resumes':resume})

@login_required
def resume_detail(request,resume_id):

    resume = get_object_or_404(Resume, id=resume_id)
    
    # Get related parsed_data entry for this resume
    parsed_resume = parsed_data.objects.filter(resume_id=resume).first()

    if not parsed_resume:
        return HttpResponse("No parsed data found for this resume.", status=404)
    
    # return HttpResponse(parsed_resume.fullname)
    return render(request, 'resumes/resume_detail.html', {'resume':parsed_resume})

@login_required
def delete_resume(request, id):
    Resume.objects.filter(id=id).update(status='7')
    return redirect('resumes_list')
