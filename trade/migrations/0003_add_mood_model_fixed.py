from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [
        ('trade', '0002_mood_alter_advice_options_and_more'),  # Depend on the existing migration
    ]

    operations = [
        migrations.CreateModel(
            name='Mood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mood', models.CharField(choices=[('confident', '😊 Confident'), ('cautious', '🤔 Cautious'), ('neutral', '😐 Neutral'), ('stressed', '😓 Stressed'), ('energetic', '⚡ Energetic'), ('tired', '😴 Tired'), ('focused', '🎯 Focused'), ('anxious', '😰 Anxious')], max_length=20)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('notes', models.CharField(blank=True, max_length=200, null=True)),
                ('trades_count', models.IntegerField(default=0)),
                ('profit_loss', models.FloatField(default=0)),
                ('win_rate', models.FloatField(default=0)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'ordering': ['-date', '-timestamp'],
                'unique_together': {('user', 'date')},
            },
        ),
    ]