# Generated by Django 5.1.7 on 2025-04-02 07:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('subscriptions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='savedcard',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_cards', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='subscriptionplan',
            name='plan_choice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_plans', to='subscriptions.planchoice'),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='saved_card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='subscriptions.savedcard'),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='subscription_plan',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='subscriptions.subscriptionplan'),
        ),
        migrations.AddField(
            model_name='usersubscription',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='savedcard',
            unique_together={('user', 'card_last4', 'expiry_month', 'expiry_year')},
        ),
    ]
