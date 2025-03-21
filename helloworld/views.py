from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(request):
    return HttpResponse("""
        <html>
            <body>
                <h1>Hello, world. You're at the index page of Spike's Sorter.</h1>
                <a href="/login/">Login</a>
            </body>
        </html>
    """)


from django.shortcuts import render, redirect
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
        
        user = authenticate(request, username=username, password=password)
        
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