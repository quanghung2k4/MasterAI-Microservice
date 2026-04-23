from django.core.management.base import BaseCommand
from posts.ai.train_model import run_training

class Command(BaseCommand):
    help = 'Chạy huấn luyện mô hình gợi ý dựa trên dữ liệu UserInteraction'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bắt đầu quá trình huấn luyện AI...'))
        run_training()
        self.stdout.write(self.style.SUCCESS('Hoàn tất!'))