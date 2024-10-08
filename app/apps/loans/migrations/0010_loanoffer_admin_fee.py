# Generated by Django 4.2.16 on 2024-09-09 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0009_loanoffer_loan_loan_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanoffer',
            name='admin_fee',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Administrative fee for the loan offer.', max_digits=10),
        ),
    ]
