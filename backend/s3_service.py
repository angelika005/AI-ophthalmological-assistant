import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
import uuid
from typing import Optional
from fastapi import UploadFile

class S3Service:
    """
    Сервис для работы с S3/MinIO хранилищем
    """
    
    def __init__(self):
        # Настройки MinIO
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "glaucoma-images")
        self.endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
        
        # Инициализация S3 клиента
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1'
        )
        
        # Проверка/создание bucket
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Проверка существования bucket, создание если не существует"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"✅ Created bucket '{self.bucket_name}'")
                except ClientError as create_error:
                    print(f"❌ Error creating bucket: {create_error}")
            else:
                print(f"❌ Error checking bucket: {e}")
    
    def upload_image(self, file: UploadFile, user_id: int) -> str:
        """
        Загружает изображение в MinIO и возвращает URL
        """
        try:
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
            unique_filename = f"users/{user_id}/{timestamp}_{unique_id}.{file_extension}"
            
            # Загружаем файл в MinIO
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                unique_filename,
                ExtraArgs={'ContentType': file.content_type or 'image/jpeg'}
            )
            
            # Формируем URL для MinIO
            url = f"{self.endpoint_url}/{self.bucket_name}/{unique_filename}"
            print(f"✅ Uploaded: {url}")
            return url
            
        except ClientError as e:
            print(f"❌ Upload error: {e}")
            raise Exception(f"Error uploading to MinIO: {str(e)}")
    
    def delete_image(self, image_url: str) -> bool:
        """
        Удаляет изображение из MinIO по URL
        """
        try:
            # Извлекаем ключ из URL
            # Формат: http://localhost:9000/bucket-name/path/to/file.jpg
            key = image_url.replace(f"{self.endpoint_url}/{self.bucket_name}/", "")
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            print(f"✅ Deleted: {key}")
            return True
            
        except ClientError as e:
            print(f"❌ Delete error: {e}")
            return False
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """
        Генерирует временный URL для приватного изображения
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"❌ Presigned URL error: {e}")
            return None

# Глобальный экземпляр сервиса
s3_service = S3Service()
