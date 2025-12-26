from django.core.mail import send_mail

def send_email_otp(email, otp):
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP is {otp}",
        from_email=None,
        recipient_list=[email],
        fail_silently=False
    )

# SMS (Twilio-ready)
def send_sms_otp(phone, otp):
    # Integrate Twilio / Fast2SMS / MSG91 here
    print(f"Send OTP {otp} to phone {phone}")
