from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
User = get_user_model()

class Expense(models.Model):
    EXPENSE_TYPES = [
        ('FOOD', 'Food'),
        ('TRAVEL', 'Travel'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('MEDICAL', 'Medical'),
        ('EDUCATION', 'Education'),
        ('HOUSING', 'Housing'),
        ('SHOPPING', 'Shopping'),
        ('VEHICLE', 'Vehicle'),
        ('INVESTMENT', 'Investment'),
        ('DUES', 'Dues'),  
        ('LENDING', 'Lending'),   
        ('GIFT', 'Gifts'),  
        ('GAMBLING', 'GAMBLING'),    
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=320, choices=EXPENSE_TYPES)
    date = models.DateField(default=date.today, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

    



class DailyIncome(models.Model):
    INCOME_TYPES = [
        ('CHEQUES', 'Cheques'),
        ('GRANTS', 'Grants'),
        ('INTEREST', 'Interest'),
        ('DIVIDENDS', 'Dividends'),
        ('GAMBLING', 'Gambling'),
        ('REFUNDS', 'Refunds (Tax)'),
        ('RENTAL', 'Rental Income'),
        ('SALE', 'Sale'),
        ('WAGES', 'Wages'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    income_type = models.CharField(max_length=50, choices=INCOME_TYPES)
    income = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user', 'date', 'income_type')

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.income_type} - ${self.income}"
    
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        Notification.objects.create(
            user = self.user,
            message = f"New income added {self.income}",
            link = "base/blog_list.html"
        )

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_already = models.DecimalField(max_digits=10, decimal_places=2)
    desired_date = models.DateField()
    note = models.TextField()

    def __str__(self):
        return f"{self.name} - {self.desired_date}"

    def clean(self):
        if self.desired_date is not None and self.desired_date < timezone.now().date():
            raise ValidationError("The desired date cannot be in the past.")
           
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return int((self.saved_already / self.target_amount) * 100)
        else:
            return 0
    
    @property
    def days_remaining(self):
        today = timezone.now().date()
        remaining_days = (self.desired_date - today).days
        return remaining_days
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Check if goal is completed
        if self.saved_already >= self.target_amount:
            Notification.objects.create(
                user=self.user,
                message=f"Congratulations! You have completed your goal: {self.name}",
                link="/path/to/goal/details"  # Adjust link as needed
            )
    
class Blog(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField(null=True, blank=True)

    def __str__(self) :
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length = 200)
    link = models.URLField(null=True,blank = True)
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return self.message




class Profile(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    profile_photo = models.ImageField(upload_to='profile_photos/', max_length=255)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)

    def __str__(self):
        return self.name

