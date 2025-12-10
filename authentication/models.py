from django.db import models

# Create your models here.

class Customer(models.Model):
    """Customer model mapping to CUSTOMER table in MySQL"""
    Customer_ID = models.AutoField(primary_key=True, db_column='Customer_ID')
    First_Name = models.CharField(max_length=255, db_column='First_Name')
    Last_Name = models.CharField(max_length=255, db_column='Last_Name')
    Mobile_No = models.CharField(max_length=50, unique=True, db_column='Mobile_No')
    Password = models.CharField(max_length=255, db_column='Password')
    Address = models.TextField(blank=True, null=True, db_column='Address')
    created_at = models.DateTimeField(null=True, blank=True, db_column='created_at')
    updated_at = models.DateTimeField(null=True, blank=True, db_column='updated_at')
    
    class Meta:
        db_table = 'CUSTOMER'
        managed = False  # Don't create migrations for this table
    
    def __str__(self):
        return f"{self.First_Name} {self.Last_Name} - {self.Mobile_No}"

class Service(models.Model):
    Service_ID = models.AutoField(primary_key=True, db_column='Service_ID')
    ServiceName = models.CharField(max_length=255, db_column='ServiceName')
    Category = models.CharField(max_length=100, db_column='Category')
    Description = models.TextField(db_column='Description', blank=True, null=True)
    Price = models.DecimalField(max_digits=10, decimal_places=2, db_column='Price')
    Original_Price = models.DecimalField(max_digits=10, decimal_places=2, db_column='Original_Price', null=True, blank=True)
    Discount_Label = models.CharField(max_length=50, db_column='Discount_Label', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_column='is_active')

    class Meta:
        db_table = 'SERVICE'
        managed = False

    def __str__(self):
        return f"{self.ServiceName} ({self.Category})"
