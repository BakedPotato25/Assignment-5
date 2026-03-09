from django.core.management.base import BaseCommand
from app.models import Book


class Command(BaseCommand):
    help = "Seed the database with 10 Vietnamese IT books"

    def handle(self, *args, **kwargs):
        Book.objects.all().delete()
        books = [
            {"title": "Kien Truc Phan Mem Hien Dai",         "author": "Nguyen Van Hung",   "price": 185000, "stock": 60},
            {"title": "Lap Trinh Python Co Ban Den Nang Cao", "author": "Tran Thi Lan",      "price": 145000, "stock": 80},
            {"title": "Clean Code - Viet Ma Nguon Sach",      "author": "Robert C. Martin",  "price": 250000, "stock": 35},
            {"title": "Thuat Toan Va Cau Truc Du Lieu",       "author": "Le Minh Hoang",     "price": 160000, "stock": 45},
            {"title": "Lap Trinh Web Voi Django 4",           "author": "Pham Quoc Dat",     "price": 130000, "stock": 90},
            {"title": "Co So Du Lieu Quan He",                "author": "Vo Thi Bich",       "price": 120000, "stock": 50},
            {"title": "Kiem Thu Phan Mem Thuc Hanh",         "author": "Dang Quang Minh",   "price": 175000, "stock": 25},
            {"title": "DevOps Va Microservices Trong Thuc Te", "author": "Hoang Duc Thanh",  "price": 220000, "stock": 40},
            {"title": "Tri Tue Nhan Tao Co Ban",              "author": "Nguyen Thi Thu",    "price": 195000, "stock": 30},
            {"title": "An Ninh Mang Va Bao Mat",              "author": "Dinh Van Long",     "price": 210000, "stock": 20},
        ]
        for data in books:
            b = Book.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f"  [+] {b.title}"))
        self.stdout.write(self.style.SUCCESS(f"Done. {len(books)} books seeded."))
