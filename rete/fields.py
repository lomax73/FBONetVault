from cryptography.fernet import Fernet
from django import forms
from django.conf import settings
from django.db import models


def _fernet():
    return Fernet(settings.MASTER_ENCRYPTION_KEY)


class EncryptedCharField(models.BinaryField):
    """Campo cifrato a riposo con Fernet (AES-128-CBC + HMAC).

    Stesso meccanismo di MKRemote/routers/fields.py e FBOPortal/catalog/
    fields.py, riusato qui per le password di accesso agli apparati e alle
    reti wireless.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', True)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.CharField, 'required': False}
        defaults.update(kwargs)
        return super(models.BinaryField, self).formfield(**defaults)

    def get_prep_value(self, value):
        if not value:
            return None
        return _fernet().encrypt(value.encode())

    def from_db_value(self, value, expression, connection):
        if value is None:
            return ''
        return _fernet().decrypt(bytes(value)).decode()

    def to_python(self, value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        return _fernet().decrypt(bytes(value)).decode()
