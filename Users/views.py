from django.shortcuts import render,redirect

# Create your views here.
# def user_reg(request):
#     return render(request,'user_reg.html')

from Users.models import User1
def user_register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        role = request.POST.get("role")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            return render(request, "user_reg.html", {"error": "Passwords do not match."})

        if User1.objects(email=email).first():
            return render(request, "user_reg.html", {"error": "An account with this email already exists."})

        user = User1(
            full_name=full_name,
            email=email,
            phone=phone,
            role=role,
            password=password1
        )
        user.save()
        return redirect('Users:login_user')

    return render(request, "user_reg.html")

#USER_LOGIN
def login_user(request):
    return render(request,"user_login.html")

def login_user_save(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User1.objects(email=email, password=password).first()

        if user:
            request.session['user_email'] = user.email
            return redirect('mysite:index')

        return render(request, "user_login.html", {"error": "Invalid email or password."})

    return render(request, "user_login.html")

#LOGOUT
def user_logout(request):
    request.session.get('user_email',None)
    return redirect("Users:login_user")

def user_profile(request):
    email = request.session.get('user_email')
    if not email:
        return redirect('Users:login_user')
    user = User1.objects(email=email).first()
    if not user:
        return redirect('Users:login_user')
    return render(request, 'user_profile.html', {'user': user})