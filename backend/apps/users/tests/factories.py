import factory
from factory.django import DjangoModelFactory
from apps.users.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "TestPass123!")
    is_verified = True
    is_active = True
    role = User.Role.USER


class UnverifiedUserFactory(UserFactory):
    is_verified = False


class AdminUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    is_staff = True
    is_superuser = True
    role = User.Role.ADMIN
