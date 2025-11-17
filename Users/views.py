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
        user_role = request.POST.get("user_role")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:
            user = User1(
                full_name=full_name,
                email=email,
                phone=phone,
                role=user_role,
                password=password1
            )
            user.save()
            return redirect('Users:login_user')  # Redirect to login page after success
        return render(request, "user_reg.html")
    return render(request, "user_reg.html")

#USER_LOGIN
def login_user(request):
    return render(request,"user_login.html")

def login_user_save(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")


        # Authenticate user from MongoDB
        user = User1.objects(email=email, password=password).first()

        if user:
            request.session['user_email'] = user.email
            request.session["user_role"] = user.role
            return redirect('mysite:index') 

        return redirect("Users:login_user")

    return render(request, "user_login.html")

#LOGOUT
def user_logout(request):
    request.session.get('user_email',None)
    request.session.flush()
    return redirect("Users:login_user")

def user_profile(request):
    data = User1.objects.all()
    return render(request,'user_profile.html',{'data':data})