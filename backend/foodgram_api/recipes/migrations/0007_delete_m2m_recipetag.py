# Generated by Django 3.2.16 on 2023-04-08 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0006_recipes_alter_tables'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='tags',
        ),
        migrations.AddField(
            model_name='recipe',
            name='tags',
            field=models.CharField(default=1, max_length=256),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='TagRecipe',
        ),
    ]
