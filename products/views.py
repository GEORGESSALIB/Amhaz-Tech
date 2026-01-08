from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render, get_object_or_404, redirect
from .models import SubCategory, Product, StockMovement, Category


def home(request):
    return render(request, 'products/index.html')

def products_by_subcategory(request, sub_id):
    subcategory = get_object_or_404(SubCategory, id=sub_id)
    products = Product.objects.filter(category=subcategory)
    return render(request, 'products/products_by_subcategory.html', {
        'subcategory': subcategory,
        'products': products
    })

# -------------------
# Stock and Product form
# -------------------
class StockForm(forms.Form):
    change = forms.IntegerField(label="Quantity")
    reason = forms.CharField(max_length=100)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'cached_quantity', 'photo']


#Product Creation
@staff_member_required
def product_add(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.category = subcategory  # assign to current subcategory
            product.save()
            return redirect('products_by_subcategory', sub_id=subcategory.id)
    else:
        form = ProductForm()

    return render(request, 'products/product_add.html', {
        'form': form,
        'subcategory': subcategory
    })

# -------------------
# Dashboard home
# -------------------
@login_required
def dashboard(request):
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    product_id = request.GET.get('product')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    categories = Category.objects.all()
    subcategories = SubCategory.objects.none()
    products = Product.objects.all()
    movements = StockMovement.objects.select_related('product')

    # -------- FILTERS --------
    if category_id:
        products = products.filter(category_id=category_id)
        subcategories = SubCategory.objects.filter(category_id=category_id)
        movements = movements.filter(product__category_id=category_id)

    if subcategory_id:
        products = products.filter(category=subcategory_id)
        movements = movements.filter(product__category=subcategory_id)

    if product_id:
        products = products.filter(id=product_id)
        movements = movements.filter(product_id=product_id)

    if date_from:
        movements = movements.filter(created_at__date__gte=date_from)

    if date_to:
        movements = movements.filter(created_at__date__lte=date_to)

    # -------- STATS --------
    total_subcategories = subcategories.count() if category_id else SubCategory.objects.count()
    total_stock = products.aggregate(Sum('cached_quantity'))['cached_quantity__sum'] or 0
    low_stock_products = products.filter(cached_quantity__lte=5)

    # -------- CHART DATA --------
    movements_by_date_qs = (
        movements
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(daily_change=Sum('change'))
        .order_by('day')
    )

    # Build cumulative total
    running_total = 0
    movements_by_date = []

    for m in movements_by_date_qs:
        running_total += m['daily_change']
        movements_by_date.append({
            'date': m['day'].strftime('%Y-%m-%d'),
            'total_stock': running_total
        })

    recent_movements = movements.order_by('-created_at')[:10]

    return render(request, 'dashboard/dashboard.html', {
        'categories': categories,
        'subcategories': subcategories,
        'products': products,
        'selected_category': category_id,
        'selected_subcategory': subcategory_id,
        'selected_product': product_id,
        'date_from': date_from,
        'date_to': date_to,
        'total_subcategories': total_subcategories,
        'total_stock': total_stock,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
        'movements_by_date': movements_by_date,
    })

# -------------------
# Add stock
# -------------------
@login_required
def add_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            change = form.cleaned_data['change']
            reason = form.cleaned_data['reason']
            StockMovement.objects.create(product=product, change=change, reason=reason)
            product.cached_quantity += change
            product.save()
            return redirect('dashboard')
    else:
        form = StockForm()
    return render(request, 'dashboard/stock_form.html', {'form': form, 'product': product, 'action': 'Add'})

# -------------------
# Remove stock
# -------------------
@login_required
def remove_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            change = form.cleaned_data['change']
            reason = form.cleaned_data['reason']
            StockMovement.objects.create(product=product, change=-change, reason=reason)
            product.cached_quantity -= change
            if product.cached_quantity < 0:
                product.cached_quantity = 0
            product.save()
            return redirect('dashboard')
    else:
        form = StockForm()
    return render(request, 'dashboard/stock_form.html', {'form': form, 'product': product, 'action': 'Remove'})
