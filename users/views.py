from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from btdyScraper.models import raceSession

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created! You can now login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    context = {
        'form': form,
        'sessions':raceSession.objects.all(),
    }

    return render(request, 'register.html', context)