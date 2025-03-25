from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Hotel, Room, Booking, RoomType, BookingStatus
from .serializers import (
    UserSerializer,
    HotelSerializer,
    HotelListSerializer,
    RoomSerializer,
    BookingSerializer,
    BookingCancelSerializer,
    RoomUpgradeSerializer
)
from django.db.models import Q
from datetime import date


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for User CRUD operations
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']


class HotelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing hotels
    """
    queryset = Hotel.objects.all().order_by('name')
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'address']

    def get_serializer_class(self):
        if self.action == 'list':
            return HotelListSerializer
        return HotelSerializer


class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing rooms
    """
    queryset = Room.objects.filter(is_active=True).order_by('hotel', 'room_number')
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['hotel', 'room_type', 'capacity']
    search_fields = ['room_number', 'description']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Endpoint to get available rooms for specific dates
        ?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD&room_type=TYPE
        """
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        room_type = request.query_params.get('room_type')

        if not check_in or not check_out:
            return Response(
                {"error": "Both check_in and check_out dates are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            check_in_date = date.fromisoformat(check_in)
            check_out_date = date.fromisoformat(check_out)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if check_in_date >= check_out_date:
            return Response(
                {"error": "Check-out date must be after check-in date"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get booked rooms for the date range
        booked_rooms = Booking.objects.filter(
            status=BookingStatus.CONFIRMED,
            check_in_date__lt=check_out_date,
            check_out_date__gt=check_in_date
        ).values_list('room_id', flat=True)

        # Filter available rooms
        queryset = Room.objects.filter(is_active=True).exclude(id__in=booked_rooms)

        if room_type and room_type in dict(RoomType.choices):
            queryset = queryset.filter(room_type=room_type)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for booking operations
    """
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'room', 'status']

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a booking
        """
        booking = self.get_object()

        if booking.status == BookingStatus.CANCELLED:
            return Response(
                {"error": "This booking is already cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BookingCancelSerializer(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data['confirm']:
                booking.cancel()
                return Response({"message": "Booking cancelled successfully"})
            else:
                return Response(
                    {"error": "Please confirm cancellation"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def upgrade_room(self, request, pk=None):
        """
        Upgrade to a different room
        """
        booking = self.get_object()

        if booking.status != BookingStatus.CONFIRMED:
            return Response(
                {"error": "Only confirmed bookings can be upgraded"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RoomUpgradeSerializer(data=request.data)
        if serializer.is_valid():
            new_room_id = serializer.validated_data['new_room_id']

            try:
                new_room = Room.objects.get(pk=new_room_id)

                # Check if new room is available for these dates
                conflicting_bookings = Booking.objects.filter(
                    room=new_room,
                    status=BookingStatus.CONFIRMED,
                    check_in_date__lt=booking.check_out_date,
                    check_out_date__gt=booking.check_in_date
                ).exclude(pk=booking.pk)

                if conflicting_bookings.exists():
                    return Response(
                        {"error": "The selected room is not available for your dates"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # If current room is SMALL and new room is not SMALL, this is an upgrade
                if booking.room.room_type == RoomType.SMALL and new_room.room_type != RoomType.SMALL:
                    success = booking.upgrade_room(new_room)
                    if success:
                        return Response({"message": "Room upgraded successfully"})
                # If current room is NORMAL and new room is LARGE, this is an upgrade
                elif booking.room.room_type == RoomType.NORMAL and new_room.room_type == RoomType.LARGE:
                    success = booking.upgrade_room(new_room)
                    if success:
                        return Response({"message": "Room upgraded successfully"})
                else:
                    return Response(
                        {"error": "The selected room is not an upgrade from your current room"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Room.DoesNotExist:
                return Response(
                    {"error": "Room not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)