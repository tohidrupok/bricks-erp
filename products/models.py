from django.db import models

class Product(models.Model):
    product_name = models.CharField(max_length=200)
    product_type = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()  # Positive integer field for quantity
    unit = models.CharField(max_length=50)  # e.g., kg, unit, piece, etc.
    rate = models.DecimalField(max_digits=10, decimal_places=2)  # Decimal field for rate
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Decimal field for amount

    def save(self, *args, **kwargs):
        # Automatically calculate the amount: quantity * rate
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name
