from django.shortcuts import render, redirect, get_object_or_404
from .models import Property
from .forms import PropertyForm
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect ('property_list')
    else:
        form = PropertyForm()
    return redirect(request, 'property/p_create.html', {'form':form})

@login_required
def property_list(request):
    properties = Property.objects.order_by('-created_at')
    return render(request, 'property/p_list.html', {'properties':properties})

@login_required
def property_detail(request, slug):
    property = get_object_or_404(Property, slug=slug)
    return render(request, 'property/p_detail.html', {'property':property})
