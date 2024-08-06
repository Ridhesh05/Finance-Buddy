from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from .models import Expense, DailyIncome,Goal,Blog,Profile
from django.contrib.auth.models import User, auth
from decimal import Decimal
import json
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from django.core.exceptions import ValidationError
from datetime import timezone
from datetime import datetime
from django.db.models import F
from django.core.paginator import Paginator
import io
import base64
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt





@login_required
def dashboard(request):
    user = request.user
    profile = Profile.objects.get(user = request.user)
    expenses = Expense.objects.filter(user=user)

    total_income = DailyIncome.objects.filter(user=user).aggregate(Sum('income'))['income__sum'] or Decimal('0')
    total_expense = expenses.exclude(type='INCOME').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    current_balance = total_income - total_expense

    expense_data = expenses.exclude(type='INCOME').values('type').annotate(total=Sum('amount'))
    expense_labels = [expense['type'] for expense in expense_data]
    expense_data_values = [float(expense['total']) for expense in expense_data]

    daily_incomes = DailyIncome.objects.filter(user=user).values('date').annotate(total=Sum('income')).order_by('date')
    income_labels = [str(income['date']) for income in daily_incomes]
    income_data_values = [float(income['total']) for income in daily_incomes]

    
    context = {
        'user': user,
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'current_balance': float(current_balance),
        'expense_labels': json.dumps(expense_labels),
        'expense_data_values': json.dumps(expense_data_values),
        'income_labels': json.dumps(income_labels),
        'income_data_values': json.dumps(income_data_values),
        'profile':profile,
    }
    return render(request, 'base/dashboard.html', context)

def log_in(request):
    if request.method=="POST":
        username=request.POST['email']
        password=request.POST['password']
        try:
            check=auth.authenticate(username=User.objects.get(email=username),password=password)
        except:
            check=auth.authenticate(username=username,password=password)
        if check is not None:
            auth.login(request,check)
            return redirect('dashboard')
        else:
            messages.info(request,'Credentials Invalid')
            return redirect('login')
        
    return render(request,'base/login.html')

@csrf_protect
def register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cnfpassword = request.POST.get('confirm_password')
        
        if password == cnfpassword:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already registered')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username already taken')
                return redirect('register')
            else:
                new_user = User.objects.create_user(username=username, email=email, password=password)
                new_user.save()
                user_login = authenticate(username=username, password=password)
                if user_login is not None:
                    login(request, user_login)
                    return redirect('dashboard')
        else:
            messages.info(request, 'Password and Confirm password do not match')
            return redirect('register')
    return render(request, 'base/register.html')

@login_required
def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def expense_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        expense_type = request.POST['type']
        amount = Decimal(request.POST['amount'])
        receipt = request.FILES.get('receipt') 
        Expense.objects.create(
            user=request.user,
            name=name,
            type=expense_type,
            amount=amount,
            receipt=receipt,
            created_at=now(),
            updated_at=now(),
        ).save()
        return redirect('dashboard')
    return render(request, 'base/add_expense.html')

@login_required
def expense_trac(request):
    user = request.user
    sort_by_expense = request.GET.get('sort_expense', 'created_at')
    order_expense = request.GET.get('order_expense', 'asc')
    sort_by_income = request.GET.get('sort_income', 'date')
    order_income = request.GET.get('order_income', 'asc')

    if order_expense == 'asc':
        expenses = Expense.objects.filter(user=user).order_by(F(sort_by_expense).asc())
    else:
        expenses = Expense.objects.filter(user=user).order_by(F(sort_by_expense).desc())

    if order_income == 'asc':
        incomes = DailyIncome.objects.filter(user=user).order_by(F(sort_by_income).asc())
    else:
        incomes = DailyIncome.objects.filter(user=user).order_by(F(sort_by_income).desc())

    #pagination for income 
    income_paginator = Paginator(incomes, 5)
    income_page_number = request.GET.get('income_page')
    income_page_obj = income_paginator.get_page(income_page_number)
    
    #paginator for expense
    expense_paginator = Paginator(expenses,5)
    expsene_page_numeber = request.GET.get('expense_page')
    expense_page_obj = expense_paginator.get_page(expsene_page_numeber)

    context ={
        'expense_page_obj': expense_page_obj,
        'income_page_obj': income_page_obj,    
        'expense_page_obj': expense_page_obj,
        'income_page_obj': income_page_obj,
        'sort_by_expense': sort_by_expense,
        'order_expense': order_expense,
        'sort_by_income': sort_by_income,
        'order_income': order_income,
    }
    
    return render(request, 'base/ExpenseTracking.html', context)

@login_required
def income_add(request):
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        income_type = request.POST['income_type']
        today = now().date()

        daily_income, created = DailyIncome.objects.update_or_create(
            user=request.user,
            date=today,
            income_type=income_type,
            defaults={'income': amount}
        )

        if not created:
            daily_income.income = amount
            daily_income.save()
        
        return redirect('dashboard')
    return render(request, 'base/add_income.html')

# @login_required
@login_required
def expense_edit(request, pk):
    expense = Expense.objects.get(pk=pk)

    if request.method == 'POST':
        expense.name = request.POST.get('name')
        expense.type = request.POST.get('type')
        expense.amount = request.POST.get('amount')
        expense.receipt = request.FILES.get('receipt')
        expense.save()
        return redirect('dashboard')

    return render(request, 'base/edit_expense.html', {'expense': expense})

@login_required
def expense_delete(request,pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('dashboard')
    return render(request, 'base/delete_expense.html', {'expense': expense})

@login_required
def goal_list(request):
    goals = Goal.objects.filter(user=request.user, saved_already__lt=F('target_amount'))
    achieved_goals = Goal.objects.filter(user=request.user, saved_already__gte=F('target_amount'))
    for goal in goals:
        
        today = date.today()
        remaining_days = (goal.desired_date - today).days
        goal.remaining_days = remaining_days
    return render(request, 'base/goal_list.html', {'goals': goals, 'achieved_goals': achieved_goals})

@login_required
def goal_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        target_amount = request.POST.get('target_amount')
        saved_already = request.POST.get('saved_already')
        date = request.POST.get('desired_date')
        note = request.POST.get('note')
       
        goal = Goal(user=request.user, name=name, target_amount=target_amount, saved_already=saved_already, 
                    desired_date=date, note=note)
        goal.save()
        return redirect('goal_list')
    return render(request, 'base/goal_add.html')

    
@login_required        
def goal_edit(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.name = request.POST.get('name')
        goal.target_amount = request.POST.get('target_amount')
        goal.saved_already = request.POST.get('saved_already')
        
        desired_date_str = request.POST.get('desired_date')
        try:
            goal.desired_date = datetime.strptime(desired_date_str, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'base/goal_add.html', {'error': 'Invalid date format', 'goal': goal})
        
        goal.note = request.POST.get('note')

        try:
            goal.clean()  
            goal.save()
            return redirect('goal_list')
        except ValidationError as e:
            return render(request, 'base/goal_add.html', {'errors': e.messages, 'goal': goal})
    return render(request, 'base/goal_add.html', {'goal': goal})




def blog_list(request):
    blogs = Blog.objects.all()
    paginator = Paginator(blogs, 5)  

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'base/blog_list.html', {'page_obj': page_obj, 'blogs': blogs})



@login_required
def predict(request):
    user = request.user
    expenses = Expense.objects.filter(user=user)
    if(expenses.count()<30*7):
        return render(request, 'base/insufficient_data.html', {'message': 'You need at least 7 months of expense data to access this feature.'})

    expense_df = pd.DataFrame(list(expenses.exclude(type='INCOME').values('created_at', 'amount')))
    
    if not expense_df.empty:
        expense_df['created_at'] = pd.to_datetime(expense_df['created_at'])
        expense_df.set_index('created_at', inplace=True)
        expense_df = expense_df.resample('D').sum()  # Daily expense aggregation

        expense_df = expense_df.asfreq('D', fill_value=0)
        expense_df['amount'] = pd.to_numeric(expense_df['amount'])

        train_size = int(len(expense_df) * 0.8)
        train, test = expense_df[0:train_size], expense_df[train_size:]

        model = ARIMA(train, order=(1, 1, 1))
        model_fit = model.fit()
        
        forecast = model_fit.forecast(steps=len(test))
        mse = mean_squared_error(test['amount'], forecast)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(test['amount'], forecast)
        full_model = ARIMA(expense_df, order=(1, 1, 1)).fit()
        forecast_next_90 = full_model.forecast(steps=90)
        forecast_labels = [(expense_df.index[-1] + pd.DateOffset(days=i)).strftime('%Y-%m-%d') for i in range(1, 91)]
        forecast_values = forecast_next_90.tolist()

        plt.figure(figsize=(10, 5))
        plt.plot(expense_df.index, expense_df['amount'], label='Historical Expenses')
        plt.plot(pd.date_range(start=expense_df.index[-1], periods=91, freq='D')[1:], forecast_next_90, label='Forecasted Expenses', linestyle='--')
        plt.xlabel('Date')
        plt.ylabel('Expense Amount')
        plt.title('Expense Forecast')
        plt.legend()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_png = buf.getvalue()
        buf.close()
        forecast_plot = base64.b64encode(image_png).decode('utf-8')
    else:
        forecast_labels = []
        forecast_values = []
        forecast_plot = None
        mse = rmse = mae = None

    context = {
        'forecast_labels': forecast_labels,
        'forecast_values': forecast_values,
        'forecast_plot': forecast_plot,
    }
    return render(request, 'base/predict.html', context)

@login_required
def profile(request):
    try:
        profile = Profile.objects.get(user = request.user)
    except ObjectDoesNotExist:
        profile = Profile(user=request.user, name=request.user.username, email=request.user.email)
    if request.method == 'POST':
        profile.name = request.user.username
        profile.email = request.user.email
        profile.dob = request.POST.get('dob',profile.dob)
        profile.gender = request.POST.get('gender',profile.gender)
        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']

        profile.save()
        return redirect('dashboard')
    context ={
        'profile': profile,
    }    
    return render(request, 'base/profile.html', context)
