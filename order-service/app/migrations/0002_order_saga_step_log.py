from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Payment Reserved", "Payment Reserved"),
                    ("Shipping Reserved", "Shipping Reserved"),
                    ("Confirmed", "Confirmed"),
                    ("Payment Failed", "Payment Failed"),
                    ("Shipping Failed", "Shipping Failed"),
                    ("Compensated", "Compensated"),
                ],
                default="Pending",
                max_length=50,
            ),
        ),
        migrations.CreateModel(
            name="SagaStepLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step", models.CharField(max_length=100)),
                ("from_status", models.CharField(blank=True, default="", max_length=50)),
                ("to_status", models.CharField(max_length=50)),
                ("success", models.BooleanField(default=True)),
                ("detail", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saga_logs",
                        to="app.order",
                    ),
                ),
            ],
        ),
    ]
