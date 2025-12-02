from django.db import models

class expenses(models.Model):
    
    EXPENSES_TYPES =[
        ('rent','Rent'),
        ('travel','Travel'),
        ('shopping','Shopping'),
        ('utilities','Utilities'),
        ('entertainment','Entertainment')
    ]
    
    date = models.DateField()
    expenses_type = models.CharField(choices=EXPENSES_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(blank=True, null=True)
    time = models.TimeField(auto_now = True)
    
    def __str__(self):
        return self.expenses_type
        