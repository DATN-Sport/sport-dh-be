import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.utils.html import strip_tags

from sport_dh.utils.enum_type import TypeEmailEnum


class TemplateMail(object):
    SUBJECT_MAIL_VERIFICATION = 'Verify your Account with OTP code'

    SUBJECT_MAIL_REGISTER_ACCOUNT = 'Verify Your Account Registration with OTP Code'

    CONTENT_MAIL_VERIFICATION = lambda full_name, otp_code: F"""<div>
    <p>Hello {full_name}</p>
    <p> We have received a request to reset the password for your Đại Hiệp - Index account. To proceed with the password reset
      process, please use the following OTP (One-Time Password) code: {otp_code}.</p>
    <p> Thank you for choosing Đại Hiệp - Index.</p>
    <p>Best regards,</p>
    <p>Đại Hiệp - Index Team</p>
  </div>"""

    CONTENT_MAIL_REGISTER_ACCOUNT = lambda full_name, otp_code: F"""<div>
    <p>Dear {full_name}</p>
    <p> Thank you for registering with Đại Hiệp - Index! To complete the registration process and verify your account,
     please use the following OTP (One-Time Password) code: {otp_code}.</p>
    <p> Thank you for choosing Velociti.</p>
    <p>Best regards,</p>
    <p>Đại Hiệp - Index Team</p>
  </div>"""


def sent_mail_verification(user, type_mail):
    random_number = random.randint(0, 9999)

    verify_code = "{:04d}".format(random_number)
    user.verify_code = verify_code
    user.code_lifetime = timezone.now() + timedelta(minutes=10)
    user.save()
    message = ""
    template_mail = ""
    if type_mail == TypeEmailEnum.REGISTER:
        message = TemplateMail.CONTENT_MAIL_REGISTER_ACCOUNT(user.full_name, verify_code)
        template_mail = TemplateMail.SUBJECT_MAIL_REGISTER_ACCOUNT
    elif type_mail == TypeEmailEnum.RESET_PASSWORD:
        message = TemplateMail.CONTENT_MAIL_VERIFICATION(user.full_name, verify_code)
        template_mail = TemplateMail.SUBJECT_MAIL_VERIFICATION
    send_mail(
        template_mail,
        strip_tags(message),
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
        html_message=message
    )
