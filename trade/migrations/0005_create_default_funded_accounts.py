# migrations/0005_create_default_funded_accounts.py
from django.db import migrations
from django.conf import settings

def create_default_accounts(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    FundedAccount = apps.get_model('trade', 'FundedAccount')
    
    for user in User.objects.all():
        # Check if user already has any funded accounts
        if not FundedAccount.objects.filter(user=user).exists():
            # Create a default account for the user
            FundedAccount.objects.create(
                user=user,
                account_name="Main Trading Account",
                account_type="OTHER",
                account_balance=10000.00,  # Default balance
                currency="USD",
                is_active=True
            )
            print(f"Created default funded account for user {user.username}")

def reverse_func(apps, schema_editor):
    # Don't delete accounts in reverse - too dangerous
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('trade', '0004_add_lot_calculator_fields_to_trades'),  # Changed from XXXX to 0004
    ]

    operations = [
        migrations.RunPython(create_default_accounts, reverse_func),
    ]