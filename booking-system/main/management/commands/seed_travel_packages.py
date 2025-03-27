from django.core.management.base import BaseCommand
from datetime import date, timedelta
from main.models import TravelPackage
import random


class Command(BaseCommand):
    help = 'Seeds the database with Travel Packages for all categories'

    def handle(self, *args, **options):
        categories = ['Adventure', 'Relaxation', 'Cultural', 'Wildlife', 'Luxury']
        destination_list = ['Maldives', 'Paris', 'New York', 'Safari Park', 'Himalayas']
        activities_list = {
            'Adventure': ['Hiking', 'Rafting', 'Skydiving', 'Climbing', 'Safari Tour'],
            'Relaxation': ['Spa', 'Beach Walk', 'Yoga', 'Resort Stay', 'Massage Therapy'],
            'Cultural': ['Museum Tours', 'Historical Sites', 'Cultural Festivals', 'Temple Visits',
                         'Local Food Tasting'],
            'Wildlife': ['Jungle Safari', 'Bird Watching', 'Animal Tracking', 'Boat Tour', 'Photography'],
            'Luxury': ['Private Beaches', 'Fine Dining', 'Yacht Tour', 'Golf', 'Exclusive Shopping']
        }

        TravelPackage.objects.all().delete()  # Clear existing packages before seeding
        self.stdout.write(self.style.SUCCESS('Existing packages deleted.'))

        package_count = 0

        for category in categories:
            for i in range(5):  # Generate 5 packages for each category
                title = f'{category} Package {i + 1}'
                description = f'This is a {category.lower()} travel package designed to offer you the best experience.'
                destination = random.choice(destination_list)
                duration_days = random.randint(3, 10)
                price = random.uniform(500, 5000)
                activities = ', '.join(random.choices(activities_list[category], k=3))
                available_from = date.today()
                available_to = date.today() + timedelta(days=180)

                TravelPackage.objects.create(
                    title=title,
                    description=description,
                    destination=destination,
                    category=category,
                    duration_days=duration_days,
                    price=round(price, 2),
                    activities=activities,
                    available_from=available_from,
                    available_to=available_to
                )

                package_count += 1

        self.stdout.write(self.style.SUCCESS(f'{package_count} travel packages created successfully.'))
