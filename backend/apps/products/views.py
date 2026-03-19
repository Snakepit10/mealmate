from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import normalize_barcode
from integrations.open_food_facts import get_product_by_barcode

from .models import Product, ProductCategory, UnitOfMeasure
from .serializers import (
    ProductSerializer,
    CreateProductSerializer,
    ProductCategorySerializer,
    UnitOfMeasureSerializer,
    BarcodeScannedProductSerializer,
)


class ProductListView(APIView):
    """GET /products/ — lista prodotti (ricerca per nome/brand)
       POST /products/ — crea prodotto manuale"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        qs = Product.objects.select_related('category', 'default_unit')
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(brand__icontains=search))
        product_type = request.query_params.get('type')
        if product_type:
            qs = qs.filter(type=product_type)
        category_id = request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)
        return Response(ProductSerializer(qs[:50], many=True).data)

    def post(self, request):
        serializer = CreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(
            created_by=request.user,
            source=Product.SOURCE_MANUAL,
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    """GET /products/{id}/  PATCH /products/{id}/"""
    permission_classes = (IsAuthenticated,)

    def _get_product(self, pk):
        try:
            return Product.objects.select_related('category', 'default_unit').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, id):
        product = self._get_product(id)
        if not product:
            return Response({'detail': 'Prodotto non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    def patch(self, request, id):
        product = self._get_product(id)
        if not product:
            return Response({'detail': 'Prodotto non trovato.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CreateProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductSerializer(product).data)


class ProductByBarcodeView(APIView):
    """GET /products/barcode/{code}/ — cerca nel DB locale per barcode"""
    permission_classes = (IsAuthenticated,)

    def get(self, request, code):
        barcode = normalize_barcode(code)
        try:
            product = Product.objects.select_related('category', 'default_unit').get(barcode=barcode)
            return Response(ProductSerializer(product).data)
        except Product.DoesNotExist:
            return Response({'found': False}, status=status.HTTP_404_NOT_FOUND)


class ProductScanView(APIView):
    """POST /products/scan/ — scansione barcode con fallback su Open Food Facts"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        barcode_raw = request.data.get('barcode', '').strip()
        if not barcode_raw:
            return Response({'detail': 'Barcode obbligatorio.'}, status=status.HTTP_400_BAD_REQUEST)

        barcode = normalize_barcode(barcode_raw)
        if not barcode:
            return Response({'detail': 'Barcode non valido.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Cerca nel DB locale
        try:
            product = Product.objects.select_related('category', 'default_unit').get(barcode=barcode)
            data = BarcodeScannedProductSerializer(product).data
            data['needs_confirmation'] = False
            return Response(data)
        except Product.DoesNotExist:
            pass

        # 2. Cerca su Open Food Facts
        off_data = get_product_by_barcode(barcode)
        if not off_data:
            return Response({'found': False}, status=status.HTTP_404_NOT_FOUND)

        # 3. Crea il prodotto nel DB locale (caching)
        category = self._resolve_category(off_data.get('category_name', ''))
        product = Product.objects.create(
            name=off_data['name'] or f'Prodotto {barcode}',
            brand=off_data.get('brand', ''),
            barcode=barcode,
            image_url=off_data.get('image_url', ''),
            nutriscore=off_data.get('nutriscore'),
            off_id=off_data.get('off_id', barcode),
            source=Product.SOURCE_OFF,
            category=category,
            created_by=request.user,
        )

        data = BarcodeScannedProductSerializer(product).data
        data['needs_confirmation'] = True
        return Response(data, status=status.HTTP_201_CREATED)

    # Mappatura parole chiave OFF → nomi categoria locale
    _OFF_CATEGORY_MAP = [
        ('Frutta e verdura',    ['fruit', 'vegetable', 'frutta', 'verdura', 'produce', 'ortaggi', 'legumi freschi']),
        ('Carne e pesce',       ['meat', 'fish', 'carne', 'pesce', 'seafood', 'poultry', 'pollame', 'salumi', 'affettati']),
        ('Latticini e uova',    ['dairy', 'milk', 'cheese', 'egg', 'latte', 'uova', 'latticini', 'formaggi', 'yogurt', 'burro', 'panna']),
        ('Pane e cereali',      ['bread', 'cereal', 'pane', 'cereali', 'bakery', 'farine', 'crackers']),
        ('Pasta, riso e legumi',['pasta', 'rice', 'riso', 'legum', 'bean', 'lentil', 'chickpea', 'ceci', 'fagioli']),
        ('Surgelati',           ['frozen', 'surgelat', 'gelato', 'ice cream']),
        ('Condimenti e salse',  ['condiment', 'sauce', 'salsa', 'dressing', 'seasoning', 'olio', 'aceto', 'spezie', 'spice', 'herb']),
        ('Bevande',             ['beverage', 'drink', 'bevande', 'water', 'acqua', 'juice', 'soda', 'coffee', 'caffè', 'tea', 'tè', 'wine', 'vino', 'beer', 'birra', 'spirits']),
        ('Snack e dolci',       ['snack', 'sweet', 'candy', 'chocolate', 'cioccolat', 'dolci', 'biscuit', 'biscotti', 'cake', 'torta', 'confection', 'caramel', 'wafer', 'chip']),
        ('Pulizia casa',        ['cleaning', 'household', 'laundry', 'pulizia', 'detergent', 'detersivo', 'paper', 'carta igienica']),
        ('Igiene personale',    ['hygiene', 'personal care', 'igiene', 'cosmetic', 'shampoo', 'soap', 'sapone', 'toothpaste', 'dentifricio', 'deodorant']),
        ('Farmaci',             ['medicine', 'drug', 'farmaci', 'health', 'supplement', 'integratori']),
    ]

    def _resolve_category(self, category_name: str):
        """Mappa la categoria OFF a una categoria locale. Non crea categorie nuove."""
        if not category_name:
            return None

        # Rimuovi prefissi lingua (es. "en:", "it:", "fr:")
        clean = category_name.lower()
        if ':' in clean:
            clean = clean.split(':', 1)[1]
        clean = clean.replace('-', ' ').strip()

        for local_name, keywords in self._OFF_CATEGORY_MAP:
            for kw in keywords:
                if kw in clean:
                    try:
                        return ProductCategory.objects.get(name__iexact=local_name)
                    except ProductCategory.DoesNotExist:
                        return None

        return None  # Nessuna corrispondenza → la view lascerà categoria vuota


class ProductCategoryListView(APIView):
    """GET /products/categories/   POST /products/categories/ (solo admin)"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        categories = ProductCategory.objects.all()
        return Response(ProductCategorySerializer(categories, many=True).data)

    def post(self, request):
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ProductCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UnitOfMeasureListView(APIView):
    """GET /products/units/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        units = UnitOfMeasure.objects.all()
        return Response(UnitOfMeasureSerializer(units, many=True).data)
