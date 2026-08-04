import factory
from factory.django import DjangoModelFactory
from apps.documents.models import Document
from apps.users.tests.factories import UserFactory


class DocumentFactory(DjangoModelFactory):
    class Meta:
        model = Document

    user = factory.SubFactory(UserFactory)
    original_filename = factory.Sequence(lambda n: f"document_{n}.pdf")
    s3_key = factory.Sequence(lambda n: f"uploads/document_{n}.pdf")
    s3_bucket = "test-bucket"
    mime_type = "application/pdf"
    file_size_bytes = 1024 * 100  # 100 KB
    status = Document.Status.PENDING
    doc_category = Document.Category.OTHER
    target_language = "en"
