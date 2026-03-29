import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cityguard.settings')
django.setup()

from reports.models import Report, Category
from django.contrib.auth import get_user_model

User = get_user_model()

def seed_data():
    # Ensure there is at least one user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@cityguard.com', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        user.set_password('admin123')
        user.save()
        print(f"Created admin user: {user.username}")

    # Create some categories if they don't exist
    categories = ['Voirie', 'Éclairage', 'Déchets', 'Eau']
    for cat_name in categories:
        Category.objects.get_or_create(name=cat_name)

    # Sample reports
    sample_reports = [
        {
            'title': 'Grand nid de poule sur l\'Avenue Hassan II',
            'description': 'Un nid de poule dangereux au milieu de la route qui cause des problèmes aux voitures.',
            'category_type': 'pothole',
            'status': 'pending',
            'severity': 'high',
            'latitude': 30.4278,
            'longitude': -9.5981,
            'address': 'Avenue Hassan II, Agadir'
        },
        {
            'title': 'Lampadaire cassé',
            'description': 'Le lampadaire ne fonctionne pas depuis trois jours, rendant la rue très sombre.',
            'category_type': 'lighting',
            'status': 'in_progress',
            'severity': 'medium',
            'latitude': 30.4212,
            'longitude': -9.5854,
            'address': 'Rue de Tiznit, Agadir'
        },
        {
            'title': 'Accumulation de déchets',
            'description': 'Beaucoup de déchets se sont accumulés près de l\'entrée du parc.',
            'category_type': 'waste',
            'status': 'resolved',
            'severity': 'low',
            'latitude': 30.4355,
            'longitude': -9.6012,
            'address': 'Quartier Industriel, Agadir'
        }
    ]

    for r_data in sample_reports:
        Report.objects.create(
            user=user,
            **r_data
        )
        print(f"Created report: {r_data['title']}")

if __name__ == '__main__':
    seed_data()
    print("Seeding complete!")
