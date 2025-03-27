from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from datetime import timedelta


class User(models.Model):
    """User model for hotel booking system without authentication"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TravelPackage(models.Model):
    CATEGORY_CHOICES = [
        ('Adventure', 'Adventure'),
        ('Relaxation', 'Relaxation'),
        ('Cultural', 'Cultural'),
        ('Wildlife', 'Wildlife'),
        ('Luxury', 'Luxury'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    destination = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Adventure')
    duration_days = models.PositiveIntegerField()  # Duration of the package in days
    price = models.DecimalField(max_digits=10, decimal_places=2)
    activities = models.TextField(help_text="List of activities separated by commas", blank=True)
    available_from = models.DateField()
    available_to = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Hotel(models.Model):
    """Hotel model with basic information"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField()
    image = models.ImageField(upload_to='hotels/', null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RoomType(models.TextChoices):
    """Room type choices"""
    SMALL = 'SMALL', _('Small')
    NORMAL = 'NORMAL', _('Normal')
    LARGE = 'LARGE', _('Large')


class Room(models.Model):
    """Room model with type and price information"""
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10)
    room_type = models.CharField(
        max_length=10,
        choices=RoomType.choices,
        default=RoomType.NORMAL
    )
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    capacity = models.PositiveIntegerField(default=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['hotel', 'room_number']

    def __str__(self):
        return f"{self.hotel.name} - Room {self.room_number} ({self.get_room_type_display()})"

    @property
    def is_available(self):
        """Check if room is available based on active bookings"""
        return self.is_active and not self.bookings.filter(
            status=BookingStatus.CONFIRMED,
            check_out_date__gt=models.functions.Now(),
            check_in_date__lte=models.functions.Now()
        ).exists()


class BookingStatus(models.TextChoices):
    """Booking status choices"""
    PENDING = 'PENDING', _('Pending')
    CONFIRMED = 'CONFIRMED', _('Confirmed')
    CANCELLED = 'CANCELLED', _('Cancelled')


class Booking(models.Model):
    """Booking model with check-in/out dates and status"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.name} - {self.room.room_number} ({self.check_in_date} to {self.check_out_date})"

    def save(self, *args, **kwargs):
        # Calculate total price if not already set
        if not self.pk and not self.total_price:
            nights = (self.check_out_date - self.check_in_date).days
            self.total_price = self.room.price_per_night * nights

        super().save(*args, **kwargs)

    def cancel(self):
        """Cancel booking"""
        self.status = BookingStatus.CANCELLED
        self.save()
        return True

    def upgrade_room(self, new_room):
        """Upgrade to a different room"""
        if new_room.is_available:
            self.room = new_room
            nights = (self.check_out_date - self.check_in_date).days
            self.total_price = new_room.price_per_night * nights
            self.save()
            return True
        return False
