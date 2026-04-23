from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0002_alter_reportresult_numeric_value"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="paid_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
