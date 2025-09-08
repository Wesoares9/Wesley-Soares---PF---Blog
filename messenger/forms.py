from django import forms
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Destinatário',
        empty_label='Escolha um usuário...',
    )

    class Meta:
        model = Message
        fields = ['receiver', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'placeholder': 'Assunto', 'class': 'form-control'}),
            'body': forms.Textarea(attrs={'placeholder': 'Escreva sua mensagem...', 'rows': 6, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Recebe `user=` ao criar a instância (na view). Usamos esse user
        para remover o próprio usuário da lista de destinatários.
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Se temos o user, exclui-o do queryset de destinatários
        if self.user is not None:
            self.fields['receiver'].queryset = User.objects.exclude(pk=self.user.pk).order_by('username')
        else:
            self.fields['receiver'].queryset = User.objects.all().order_by('username')

    def clean_receiver(self):
        ##Evita envio para si mesmo caso alguém tente manipular o formulário.
        receiver = self.cleaned_data.get('receiver')
        if self.user and receiver == self.user:
            raise forms.ValidationError('Você não pode enviar uma mensagem para si mesmo.')
        return receiver
