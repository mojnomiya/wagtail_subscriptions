# Generated migration for wagtail_subscriptions

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(blank=True, max_length=255)),
                ('billing_email', models.EmailField(blank=True, max_length=254)),
                ('tax_id', models.CharField(blank=True, max_length=100, verbose_name='Tax ID')),
                ('address_line1', models.CharField(blank=True, max_length=255)),
                ('address_line2', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('state', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
            },
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Module Name')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('icon', models.CharField(blank=True, help_text='CSS icon class', max_length=50)),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Sort Order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Module',
                'verbose_name_plural': 'Modules',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Plan Name')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Price')),
                ('billing_period', models.CharField(choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly'), ('lifetime', 'Lifetime')], default='monthly', max_length=20)),
                ('trial_period_days', models.PositiveIntegerField(default=0, verbose_name='Trial Period (days)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Sort Order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Subscription Plan',
                'verbose_name_plural': 'Subscription Plans',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Feature Name')),
                ('slug', models.SlugField(verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('feature_type', models.CharField(choices=[('binary', 'Binary (On/Off)'), ('quota', 'Quota (Usage Limit)'), ('tiered', 'Tiered (Multiple Levels)')], default='binary', max_length=20)),
                ('default_quota', models.PositiveIntegerField(blank=True, null=True, verbose_name='Default Quota')),
                ('quota_unit', models.CharField(blank=True, max_length=50, verbose_name='Quota Unit')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Sort Order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='wagtail_subscriptions.module')),
            ],
            options={
                'verbose_name': 'Feature',
                'verbose_name_plural': 'Features',
                'ordering': ['module', 'sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('trialing', 'Trialing'), ('active', 'Active'), ('past_due', 'Past Due'), ('canceled', 'Canceled'), ('unpaid', 'Unpaid')], default='trialing', max_length=20)),
                ('current_period_start', models.DateTimeField()),
                ('current_period_end', models.DateTimeField()),
                ('trial_end', models.DateTimeField(blank=True, null=True)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('external_id', models.CharField(blank=True, max_length=255, verbose_name='External ID')),
                ('payment_processor', models.CharField(default='stripe', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='wagtail_subscriptions.subscriptionplan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
            },
        ),
        migrations.CreateModel(
            name='PlanFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_included', models.BooleanField(default=True, verbose_name='Included')),
                ('quota_override', models.PositiveIntegerField(blank=True, null=True, verbose_name='Quota Override')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_features', to='wagtail_subscriptions.feature')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_features', to='wagtail_subscriptions.subscriptionplan')),
            ],
            options={
                'verbose_name': 'Plan Feature',
                'verbose_name_plural': 'Plan Features',
            },
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['user', 'status'], name='wagtail_sub_user_id_b8e5c7_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['external_id'], name='wagtail_sub_externa_4b8c8a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='planfeature',
            unique_together={('plan', 'feature')},
        ),
        migrations.AlterUniqueTogether(
            name='feature',
            unique_together={('module', 'slug')},
        ),
    ]