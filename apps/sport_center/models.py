from io import BytesIO

from PIL import Image
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.db import models

from apps.user.models import User
from apps.utils.enum_type import StatusFieldEnum, SportTypeEnum


class SportCenter(models.Model):
    owner = models.ForeignKey(User, null=False, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=True)
    address = models.CharField(max_length=255, null=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "owner": self.owner.full_name if self.owner else "None",
            "name": self.name,
            "address": self.address,
        }

class SportField(models.Model):
    sport_center = models.ForeignKey(SportCenter, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=True)
    address = models.CharField(max_length=255, null=False, blank=True)
    sport_type = models.CharField(max_length=255, choices=SportTypeEnum.choices(), default=SportTypeEnum.FOOTBALL)
    price = models.FloatField(null=False, blank=True)
    status = models.CharField(max_length=255, choices=StatusFieldEnum.choices(), default=StatusFieldEnum.INACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sport_center": self.sport_center.name,
            "name": self.name,
            "sport_type": self.sport_type,
            "price": self.price,
            "status": self.status,
        }


class ImageSport(models.Model):
    file = models.ImageField(upload_to='images/')
    preview = models.ImageField(upload_to='images/preview/', null=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        if self.file and not self.preview:
            self.preview = self.create_preview(self.file)
        super().save(*args, **kwargs)

    def create_preview(self, image_field, max_size=(300, 300), quality=70):
        """
        Args:
            image_field: ImageField object
            max_size: Kích thước tối đa (width, height)
            quality: Chất lượng ảnh (1-100), thấp hơn = nhẹ hơn
        """
        try:
            img = Image.open(image_field)

            # Chuyển đổi RGBA sang RGB nếu cần (cho JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            thumb_io = BytesIO()
            img.save(thumb_io, format='JPEG', quality=quality, optimize=True)
            thumb_io.seek(0)

            original_name = image_field.name.split('/')[-1]
            name_parts = original_name.rsplit('.', 1)
            preview_name = f"{name_parts[0]}_preview.jpg"

            return ContentFile(thumb_io.read(), name=preview_name)

        except Exception as e:
            print(f"Error creating preview: {e}")
            return None


