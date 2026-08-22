from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eleves', '0002_ecole_alter_classe_options_niveau_code_niveau_cycle_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupeScolaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, default='Groupe Scolaire')),
                ('sigle', models.CharField(max_length=20, blank=True)),
                ('adresse', models.TextField(blank=True)),
                ('telephone', models.CharField(max_length=30, blank=True)),
                ('email', models.EmailField(blank=True)),
                ('site_web', models.URLField(blank=True)),
                ('logo', models.ImageField(upload_to='groupe/logo/', blank=True, null=True)),
                ('devise', models.CharField(max_length=200, blank=True, help_text='Slogan ou devise')),
                ('bp', models.CharField(max_length=50, blank=True, verbose_name='Boîte postale')),
                ('ville', models.CharField(max_length=100, blank=True)),
                ('pays', models.CharField(max_length=100, default='Côte d\'Ivoire')),
            ],
            options={
                'verbose_name': 'Groupe scolaire',
            },
        ),
    ]
