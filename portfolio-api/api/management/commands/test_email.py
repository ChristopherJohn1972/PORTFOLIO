import smtplib
import ssl
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test SMTP email connection'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== SMTP Connection Test ==='))
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: [{settings.EMAIL_HOST_USER}]')
        self.stdout.write(f'EMAIL_HOST_PASSWORD: [***] (len={len(settings.EMAIL_HOST_PASSWORD)})')
        self.stdout.write(f'CONTACT_RECEIVER_EMAIL: {settings.CONTACT_RECEIVER_EMAIL}')
        self.stdout.write('')

        # Step 1: Connect
        try:
            self.stdout.write('Step 1: Connecting to SMTP server...')
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15)
            self.stdout.write(self.style.SUCCESS(f'  Connected to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED to connect: {type(e).__name__}: {e}'))
            return

        # Step 2: EHLO
        try:
            self.stdout.write('Step 2: Sending EHLO...')
            ehlo_resp = server.ehlo()
            self.stdout.write(self.style.SUCCESS(f'  EHLO response code: {ehlo_resp[0]}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  EHLO failed: {e}'))
            server.quit()
            return

        # Step 3: STARTTLS
        try:
            self.stdout.write('Step 3: Starting TLS...')
            tls_resp = server.starttls()
            self.stdout.write(self.style.SUCCESS(f'  TLS started, response: {tls_resp[0]}'))
            server.ehlo()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  TLS failed: {e}'))
            server.quit()
            return

        # Step 4: Login
        try:
            self.stdout.write('Step 4: Logging in...')
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS('  LOGIN SUCCESSFUL'))
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(self.style.ERROR(f'  AUTH FAILED: {e}'))
            self.stdout.write(self.style.ERROR(''))
            self.stdout.write(self.style.ERROR('POSSIBLE CAUSES:'))
            self.stdout.write(self.style.ERROR('  1. Wrong app password — go to https://myaccount.google.com/apppasswords'))
            self.stdout.write(self.style.ERROR('  2. 2-Step Verification not enabled — go to https://myaccount.google.com/security'))
            self.stdout.write(self.style.ERROR('  3. Email address does not match the Google account'))
            self.stdout.write(self.style.ERROR('  4. App password was revoked/deleted'))
            server.quit()
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  LOGIN FAILED: {type(e).__name__}: {e}'))
            server.quit()
            return

        # Step 5: Send test email
        try:
            self.stdout.write('Step 5: Sending test email...')
            from_email = settings.EMAIL_HOST_USER
            to_email = settings.CONTACT_RECEIVER_EMAIL
            subject = 'Portfolio SMTP Test'
            body = 'This is a test email from your portfolio.'
            message = f'Subject: {subject}\nFrom: {from_email}\nTo: {to_email}\n\n{body}'
            server.sendmail(from_email, to_email, message)
            self.stdout.write(self.style.SUCCESS(f'  EMAIL SENT to {to_email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  SEND FAILED: {type(e).__name__}: {e}'))
            server.quit()
            return

        server.quit()
        self.stdout.write(self.style.SUCCESS(''))
        self.stdout.write(self.style.SUCCESS('=== ALL STEPS PASSED — Check your inbox/spam ==='))
