from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0003_report_paid_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="sample_collected_by_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
