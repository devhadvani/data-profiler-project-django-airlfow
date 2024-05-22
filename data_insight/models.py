from django.db import models
# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from datetime import datetime
from cryptography.fernet import Fernet
# from .helper import encrypt_data, decrypt_data

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    first_name = models.CharField(max_length=30,blank=True)
    last_name = models.CharField(max_length=30,blank=True)
    email = models.EmailField(max_length=100,unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

class ConnectionDetails(models.Model):
    project = models.OneToOneField('Project', on_delete=models.CASCADE, related_name='connection_details')
    connector_type = models.CharField(max_length=100)
    host = models.CharField(max_length=100)
    port = models.IntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # Field to store the encrypted password
    database_name = models.CharField(max_length=100)

    # def set_encrypted_password(self, password):
    #     self.password = encrypt_data(password)

    # def get_decrypted_password(self):
    #     return decrypt_data(self.password)

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    visibility = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], default='private')
    pipeline = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class TestResult(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)  # ForeignKey to Project model
    table_name = models.CharField(max_length=100)
    total_row = models.CharField(max_length=100)
    total_column =  models.CharField(max_length=100)
    data_types = models.JSONField()
    missing_values = models.JSONField()
    unique_values = models.JSONField()
    descriptive_statistics = models.JSONField()
    data_quality_issues = models.JSONField()
    correlation_coefficients = models.JSONField()
    outliers = models.JSONField()
    created_at = models.DateTimeField() 
    updated_at = models.DateTimeField() 


    class Meta:
        db_table = 'testresult'





# class TestResults(models.Model):
#     id = models.AutoField(primary_key=True)
#     project = models.ForeignKey(Project, on_delete=models.CASCADE)  
#     table_name = models.CharField(max_length=100)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

# class DataType(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column_name = models.CharField(max_length=100)
#     data_type = models.CharField(max_length=100)

# class MissingValue(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column_name = models.CharField(max_length=100)
#     value = models.CharField(max_length=100)  

# class UniqueValue(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column_name = models.CharField(max_length=100)
#     value = models.CharField(max_length=100)  

# class DescriptiveStatistic(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column_name = models.CharField(max_length=100)
#     mean = models.FloatField()
#     std_dev = models.FloatField()
#     min_val = models.FloatField()
#     max_val = models.FloatField()

# class DataQualityIssue(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column_name = models.CharField(max_length=100)
#     value = models.CharField(max_length=100) 

# class CorrelationCoefficient(models.Model):
#     test_result = models.ForeignKey(TestResults, on_delete=models.CASCADE)
#     column1_name = models.CharField(max_length=100)
#     column2_name = models.CharField(max_length=100)
#     coefficient = models.FloatField()






#for to store user's data in our database

class ProjectTable(models.Model):
    project_id = models.IntegerField() 
    table_name = models.CharField(max_length=100)

    def __str__(self):
        return self.table_name


class ProjectTableColumn(models.Model):
    table = models.ForeignKey(ProjectTable, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100)
    data_type = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name

class ProjectTableRow(models.Model):
    project_table = models.ForeignKey(ProjectTable, on_delete=models.CASCADE, related_name='rows')
    row_data = models.TextField()

    def __str__(self):
        return f"Row for {self.project_table.table_name}"
        

class Testrow(models.Model):
    total_row = models.CharField(max_length=100)
    total_column = models.CharField(max_length=100)
