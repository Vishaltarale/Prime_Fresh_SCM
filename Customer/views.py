from django.shortcuts import render,HttpResponse,redirect
# from 

# # Create your views here.

# def customer_register(request):
#     return render(request,"customer_register.html")

# def Customer_save(request):
#     if request.method == "POST":
#         first_name = request.POST['first_name']
#         last_name = request.POST['last_name']
#         email = request.POST['email']
#         company_name = request.POST['company_name']
#         phone_number = request.POST['phone_number']
#         address = request.POST['address']
#         password1 = request.POST['password1']
#         password2 = request.POST['password2']
        
#         s = Customers(first_name=first_name,last_name=last_name,email=email,company_name=company_name,phone_number=phone_number,address=address,password=password1,confirm_password=password2)
#         s.save()
#         return redirect("mysite:index")
#     return redirect("Customer:Customer_register")
