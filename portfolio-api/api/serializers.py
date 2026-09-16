from rest_framework import serializers
from .models import ContactRequest, CVRequest, ProjectLinkRequest


class ContactRequestSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    _gotcha = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = ContactRequest
        fields = [
            'first_name', 'last_name', 'company', 'email', 'opportunity_type',
            'position', 'message', '_gotcha',
        ]

    def validate_first_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

    def validate_company(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Company must be at least 2 characters.")
        return value.strip()

    def validate_email(self, value):
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.strip().lower()

    def validate_opportunity_type(self, value):
        valid = ['Job Opportunity', 'Contract Opportunity', 'Freelance Project',
                 'Internship / Training', 'Technical Collaboration', 'Other']
        if value not in valid:
            raise serializers.ValidationError("Select a valid opportunity type.")
        return value

    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message must be under 5000 characters.")
        return value.strip()

    def validate(self, data):
        honeypot = data.pop('_gotcha', None)
        if honeypot:
            data['honeypot_hit'] = True
        data['full_name'] = f"{data.pop('first_name')} {data.pop('last_name')}"
        return data


class CVRequestSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    _gotcha = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = CVRequest
        fields = [
            'first_name', 'last_name', 'company', 'email', 'position',
            'message', '_gotcha',
        ]

    def validate_first_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

    def validate_company(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Company must be at least 2 characters.")
        return value.strip()

    def validate_email(self, value):
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.strip().lower()

    def validate_position(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Position must be at least 2 characters.")
        return value.strip()

    def validate_message(self, value):
        if value and len(value) > 5000:
            raise serializers.ValidationError("Message must be under 5000 characters.")
        return value.strip() if value else ''

    def validate(self, data):
        honeypot = data.pop('_gotcha', None)
        if honeypot:
            data['honeypot_hit'] = True
        data['full_name'] = f"{data.pop('first_name')} {data.pop('last_name')}"
        return data


class ProjectLinkRequestSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    _gotcha = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = ProjectLinkRequest
        fields = [
            'first_name', 'last_name', 'company', 'email', 'projects',
            'message', '_gotcha',
        ]

    def validate_first_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("First name is required.")
        return value.strip()

    def validate_last_name(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

    def validate_company(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Company must be at least 2 characters.")
        return value.strip()

    def validate_email(self, value):
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.strip().lower()

    def validate_projects(self, value):
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("Select at least one project.")
        valid = ['CRM', 'Rental Management System', 'All Featured Projects',
                 'GitHub Profile', 'Other']
        for p in value:
            if p not in valid:
                raise serializers.ValidationError(f"Invalid project: {p}")
        return value

    def validate_message(self, value):
        if value and len(value) > 5000:
            raise serializers.ValidationError("Message must be under 5000 characters.")
        return value.strip() if value else ''

    def validate(self, data):
        honeypot = data.pop('_gotcha', None)
        if honeypot:
            data['honeypot_hit'] = True
        data['full_name'] = f"{data.pop('first_name')} {data.pop('last_name')}"
        return data
