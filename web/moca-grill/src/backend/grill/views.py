from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import Shop, MenuItem, Order, Review
from .serializers import ShopSerializer, MenuItemSerializer, CreateMenuItemSerializer, OrderSerializer, CreateOrderSerializer, ReviewSerializer, ApproveReviewSerializer, CreateReviewSerializer


class ShopView(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    serializer_class = ShopSerializer

    def get_queryset(self):
        return Shop.objects.all()

    @action(detail=True, methods=['GET'])
    def review(self, request, pk=None):
        shop = self.get_object()
        reviews = Review.objects.filter(order__shop=shop, approved=True)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ShopItemsView(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):

    serializer_class = MenuItemSerializer

    def get_queryset(self):
        return MenuItem.objects.filter(shop=self.kwargs['shop_pk'])

    def create(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        shop = Shop.objects.filter(pk=self.kwargs['shop_pk'], owner=request.user).first()

        if not shop:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CreateMenuItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(shop=shop)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderView(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @action(detail=True, methods=['POST'])
    def review(self, request, pk=None):
        order = self.get_object()

        if not order:
            return Response(status=status.HTTP_404_NOT_FOUND)

        data = request.data
        data['order'] = order.pk
        data['user'] = request.user.pk

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderCreateView(mixins.CreateModelMixin, viewsets.GenericViewSet):

    serializer_class = CreateOrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        request.data['shop'] = self.kwargs['shop_pk']
        request.data['user'] = request.user.pk
        serializer = CreateOrderSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ManageReviewView(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(order__shop__owner=self.request.user)


    def update(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        review = self.get_object()

        if not review:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ApproveReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data)


    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().retrieve(request, *args, **kwargs)


    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)

        qs = self.get_queryset()
        qs = qs.filter(**request.query_params.dict())
        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data)