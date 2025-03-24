from rest_framework import serializers
from .models import User, Hotel, Room, Booking, RoomType, BookingStatus


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'address', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class RoomSerializer(serializers.ModelSerializer):
    hotel_name = serializers.StringRelatedField(source='hotel.name', read_only=True)
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)

    class Meta:
        model = Room
        fields = [
            'id', 'hotel', 'hotel_name', 'room_number', 'room_type', 'room_type_display',
            'price_per_night', 'capacity', 'description', 'is_active', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_available']


class HotelSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)

    class Meta:
        model = Hotel
        fields = [
            'id', 'name', 'address', 'description', 'image', 'rating',
            'rooms', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class HotelListSerializer(serializers.ModelSerializer):
    room_count = serializers.IntegerField(source='rooms.count', read_only=True)

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'address', 'rating', 'image', 'room_count']


class BookingSerializer(serializers.ModelSerializer):
    user_name = serializers.StringRelatedField(source='user.name', read_only=True)
    room_info = serializers.StringRelatedField(source='room', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'user_name', 'room', 'room_info', 'check_in_date',
            'check_out_date', 'status', 'status_display', 'total_price', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_price']

    def validate(self, data):
        """
        Validate the booking data:
        - Check-out date must be after check-in date
        - Room must be available for the requested dates
        """
        if data['check_in_date'] >= data['check_out_date']:
            raise serializers.ValidationError("Check-out date must be after check-in date")

        # Check if room is available for the dates
        room = data['room']
        check_in = data['check_in_date']
        check_out = data['check_out_date']

        # Get conflicting bookings
        conflicting_bookings = Booking.objects.filter(
            room=room,
            status=BookingStatus.CONFIRMED,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )

        # Exclude current booking if updating
        current_booking_id = self.instance.id if self.instance else None
        if current_booking_id:
            conflicting_bookings = conflicting_bookings.exclude(id=current_booking_id)

        if conflicting_bookings.exists():
            raise serializers.ValidationError(
                "This room is not available for the selected dates"
            )

        return data


class BookingCancelSerializer(serializers.Serializer):
    confirm = serializers.BooleanField(required=True)


class RoomUpgradeSerializer(serializers.Serializer):
    new_room_id = serializers.IntegerField(required=True)

    def validate_new_room_id(self, value):
        try:
            room = Room.objects.get(pk=value)
            if not room.is_active:
                raise serializers.ValidationError("The selected room is not active")
            return value
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room not found")