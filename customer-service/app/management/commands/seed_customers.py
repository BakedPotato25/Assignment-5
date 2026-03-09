from django.core.management.base import BaseCommand
from app.models import Customer


class Command(BaseCommand):
    help = "Seed the database with 10 Vietnamese customers"

    def handle(self, *args, **kwargs):
        Customer.objects.all().delete()
        customers = [
            {"name": "Nguyen Van An",      "email": "vanan.nguyen@gmail.com"},
            {"name": "Tran Thi Bich",      "email": "bichtran.hcm@gmail.com"},
            {"name": "Le Hoang Nam",       "email": "namle.ptit@gmail.com"},
            {"name": "Pham Quoc Toan",     "email": "toanbk@outlook.com"},
            {"name": "Vo Thi Mai Anh",     "email": "maianh.vo@yahoo.com"},
            {"name": "Dang Minh Khoa",     "email": "khoabk19@gmail.com"},
            {"name": "Hoang Duc Hieu",     "email": "duchieu.hoang@fpt.edu.vn"},
            {"name": "Bui Thi Lan",        "email": "lanbui.hust@gmail.com"},
            {"name": "Do Van Cuong",       "email": "cuongdo.dev@gmail.com"},
            {"name": "Nguyen Thi Thanh",   "email": "thanhnt.ute@gmail.com"},
        ]
        for data in customers:
            c = Customer.objects.create(**data)
            self.stdout.write(self.style.SUCCESS(f"  [+] {c.name} <{c.email}>"))
        self.stdout.write(self.style.SUCCESS(f"Done. {len(customers)} customers seeded."))
