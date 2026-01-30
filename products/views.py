from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import SubCategory, Product, StockMovement, Category


def home(request):
    return render(request, 'products/index.html')


def products_by_subcategory(request, sub_id):
    subcategory = get_object_or_404(SubCategory, id=sub_id)

    products = Product.objects.filter(category=subcategory)

    if not request.user.is_staff:
        products = products.filter(is_active=True)

    return render(request, 'products/products_by_subcategory.html', {
        'subcategory': subcategory,
        'products': products,
    })


def product_search(request):
    search_query = request.GET.get('q', '').strip()

    products = Product.objects.all()

    if not request.user.is_staff:
        products = products.filter(is_active=True)

    if search_query:
        products = products.filter(
            name__icontains=search_query
        )

    return render(request, 'products/product_search.html', {
        'products': products,
        'search_query': search_query,
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
        fields = ['name', 'description', 'price', 'cached_quantity', 'photo', 'is_active']

# -------------------
# Category and SubCategory form
# -------------------
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

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
@staff_member_required
def dashboard(request):
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    product_id = request.GET.get('product')

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


    # -------- STATS --------
    total_subcategories = subcategories.count() if category_id else SubCategory.objects.count()
    total_stock = products.aggregate(Sum('cached_quantity'))['cached_quantity__sum'] or 0
    low_stock_products = products.filter(cached_quantity__lte=5)


    recent_movements = movements.order_by('-created_at')[:10]

    return render(request, 'dashboard/dashboard.html', {
        'categories': categories,
        'subcategories': subcategories,
        'products': products,
        'selected_category': category_id,
        'selected_subcategory': subcategory_id,
        'selected_product': product_id,
        'total_subcategories': total_subcategories,
        'total_stock': total_stock,
        'low_stock_products': low_stock_products,
        'recent_movements': recent_movements,
    })

def ajax_subcategories(request):
    category_id = request.GET.get("category")
    subs = SubCategory.objects.filter(category_id=category_id).values("id", "name")
    return JsonResponse(list(subs), safe=False)


def ajax_products(request):
    category_id = request.GET.get("category")
    subcategory_id = request.GET.get("subcategory")

    qs = Product.objects.all()

    if category_id:
        qs = qs.filter(category_id=category_id)
    if subcategory_id:
        qs = qs.filter(category_id=subcategory_id)

    products = qs.values("id", "name")
    return JsonResponse(list(products), safe=False)

# -------------------
# Add stock
# -------------------
@staff_member_required
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
@staff_member_required
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


@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)

        # 🔒 lock stock
        form.fields["cached_quantity"].disabled = True

        if form.is_valid():
            form.save()
            return redirect("products_by_subcategory", product.category.id)
    else:
        form = ProductForm(instance=product)

        # 🔒 lock stock
        form.fields["cached_quantity"].disabled = True

    return render(request, "products/product_form.html", {
        "form": form,
        "product": product,
    })

# ================= CATEGORY =================
@staff_member_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'staff/category_list.html', {'categories': categories})

@staff_member_required
def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'staff/category_form.html', {'form': form, 'title': 'Add Category'})

@staff_member_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'staff/category_form.html', {'form': form, 'title': 'Edit Category'})


# ================= SUBCATEGORY =================
@staff_member_required
def subcategory_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    subcategories = category.subcategory_set.all()
    return render(request, 'staff/subcategory_list.html', {
        'category': category,
        'subcategories': subcategories
    })

@staff_member_required
def subcategory_add(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            subcat = form.save(commit=False)
            subcat.category = category
            subcat.save()
            return redirect('subcategory_list_by_category', category_id=category.id)
    else:
        form = SubCategoryForm(initial={'category': category})
    return render(request, 'staff/subcategory_form.html', {'form': form, 'title': 'Add SubCategory', 'category': category})

@staff_member_required
def subcategory_edit(request, subcategory_id):
    subcategory = get_object_or_404(SubCategory, id=subcategory_id)
    category = subcategory.category  # get parent category

    if request.method == 'POST':
        form = SubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            form.save()
            # Redirect back to subcategory list for this category
            return redirect('subcategory_list_by_category', category_id=category.id)
    else:
        form = SubCategoryForm(instance=subcategory)

    return render(
        request,
        'staff/subcategory_form.html',
        {
            'form': form,
            'title': 'Edit SubCategory',
            'category': category
        }
    )


