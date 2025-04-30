from django.db import models
from django.contrib.auth.models import User  # If you plan to implement user accounts

class Dataset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Link to user if you have accounts
    name = models.CharField(max_length=255, blank=True, null=True, help_text="Optional name for the dataset")
    uploaded_file = models.FileField(upload_to='datasets/')  # Store the uploaded file
    upload_date = models.DateTimeField(auto_now_add=True)
        # Temporary field - remove after migrations
    #temp_field = models.BooleanField(default=False)

    def __str__(self):
        return f"Dataset object ({self.id})"

class Transaction(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='transactions')
    posting_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reconcile = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name if self.name else f"Dataset uploaded on {self.upload_date}"

# Create your models here.
