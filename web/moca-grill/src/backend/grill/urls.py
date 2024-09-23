from django.urls import path, include
from .views import ShopView, ShopItemsView, OrderView, OrderCreateView, ManageReviewView
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

router = SimpleRouter()
router.register(
    r'shop',
    ShopView,
    basename='shop'
)
router.register(
    r'order',
    OrderView,
    basename='order'
)
router.register(
    r'manage',
    ManageReviewView,
    basename='manage'
)

shop_router = NestedSimpleRouter(router, r'shop', lookup='shop')
shop_router.register(
    r'menu',
    ShopItemsView,
    basename='shop-menu'
)
shop_router.register(
    r'order',
    OrderCreateView,
    basename='shop-order'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(shop_router.urls)),
]