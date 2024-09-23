from rest_framework import serializers

from .models import Shop, MenuItem, Order, Review, OrderItem

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'


class CreateMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            'name',
            'description',
            'price'
        ]


class CreateOrderItemSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ['item', 'quantity']


class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='item.name', read_only=True)
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ['name', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    shop_name = serializers.CharField(source='shop.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'items',
            'total',
            'shop_name'
        ]


class CreateOrderSerializer(serializers.ModelSerializer):
    items = CreateOrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'items',
            'shop',
            'user'
        ]

    def validate(self, data):
        items_data = data.pop('items')
        shop = data['shop']

        if not items_data:
            raise serializers.ValidationError("Order must contain at least one item.")

        compacted_items_data = {}

        for item in items_data[:10]:
            if item['quantity'] <= 0:
                raise serializers.ValidationError("Quantity must be greater than zero.")
            if item['item'].shop != shop:
                raise serializers.ValidationError("All items must be from the same shop.")
            
            if item['item'].id in compacted_items_data:
                compacted_items_data[item['item'].id]['quantity'] += item['quantity']
            else:
                compacted_items_data[item['item'].id] = item

        data['items'] = compacted_items_data.values()
        data['total'] = sum(item['item'].price * item['quantity'] for item in data['items'])

        return data


    def create(self, validated_data):
        user = validated_data['user']

        items_data = validated_data.pop('items')
        shop = validated_data['shop']
        total = validated_data['total']

        # Create the order with the provided user, shop, and total
        order = Order.objects.create(user=user, shop=shop, total=total)

        # Create the order items
        for item_data in items_data:
            OrderItem.objects.create(order=order, item=item_data['item'], quantity=item_data['quantity'])

        return order


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Review
        fields = '__all__'


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'rating',
            'comment',
            'order',
            'user',
        ]


class ApproveReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'approved'
        ]