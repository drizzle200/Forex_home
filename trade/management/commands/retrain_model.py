from django.core.management.base import BaseCommand
from trade.utils import train_model

class Command(BaseCommand):
    help = 'Retrain the ML model using current global training data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting model retraining...'))
        
        model = train_model()
        
        if model:
            self.stdout.write(self.style.SUCCESS('✅ Model retrained successfully!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Model training failed. Check global training data.'))