from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from resumes.models import Resume
from jobs.models import JobListing
from matching.models import MatchResult, SavedJobs
from django.db.models import Exists, OuterRef, Value, BooleanField, Subquery, Count

User = get_user_model()
# Create your views here.
def anonymous_required(view_func):
    return user_passes_test(lambda u: not u.is_authenticated, login_url='dashboard')(view_func)

@anonymous_required
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "You have been Logged in.")
            return redirect('/')
        
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})    
    # return HttpResponse(f"Django is using: {User.__module__}.{User.__name__}")
@anonymous_required
def register(request):
    if(request.method == 'POST'):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(request, "Your account as been created, please Login to continue.")
            return redirect('login')
        
    else:
        form = RegisterForm()

    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def dashboard(request):
    resume_count_subquery = Resume.objects.filter(
        user_id=OuterRef('user_id')
    ).values('user_id').annotate(
        total=Count('id')
    ).values('total')

    # Main query
    resume_total = Resume.objects.filter(user_id=request.user, status='2').count()

    jobs = (
        MatchResult.objects
        .select_related('job', 'resume', 'user')
        .annotate(resume_count=Subquery(resume_count_subquery))
        .filter(user=request.user, resume__status='2')
    )

    data = {
        'user': request.user,
        'resumes': resume_total,
        'jobs': jobs.count(),
    }
    # print(data)



    return render(request, 'dashboard/dashboard.html', {'data': data})
    
def logout_view(request):
    logout(request)
    messages.success(request, "You have been Logged out.")
    return redirect('login')


