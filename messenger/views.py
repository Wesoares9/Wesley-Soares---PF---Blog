from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message
from .forms import MessageForm
from django.contrib import messages

@login_required
def inbox(request):
    msgs = request.user.received_messages.order_by('-created_at')
    return render(request, 'messenger/inbox.html', {'messages': msgs})

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.sender = request.user
            m.save()
            messages.success(request, 'Mensagem enviada!')
            return redirect('inbox')
    else:
        form = MessageForm()
    return render(request, 'messenger/send.html', {'form': form})

@login_required
def message_detail(request, pk):
    msg = get_object_or_404(Message, pk=pk, receiver=request.user)
    msg.is_read = True
    msg.save()
    return render(request, 'messenger/detail.html', {'message': msg})

