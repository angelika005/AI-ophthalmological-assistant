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
        self.skip_init = os.getenv("S3_SKIP_INIT", "0") == "1"
        
        # Инициализация S3 клиента
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1'
        )
        
        # Проверка/создание bucket (можно отключить в тестах)
        if not self.skip_init:
            self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Проверка существования bucket, создание если не существует"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"Created bucket '{self.bucket_name}'")
                except ClientError as create_error:
                    print(f"Error creating bucket: {create_error}")
            else:
                print(f"Error checking bucket: {e}")

        # Делаем bucket приватным: удаляем публичную bucket policy, если она была настроена ранее.
        try:
            self.s3_client.delete_bucket_policy(Bucket=self.bucket_name)
            print(f"Removed bucket policy for '{self.bucket_name}' (private access)")
        except ClientError:
            # Политики могло не быть - это нормальный случай.
            pass
    
    def _set_public_policy(self):
        """Устанавливает публичную политику для bucket (только для чтения)"""
        import json
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(policy)
            )
            print(f"Public read policy set for bucket '{self.bucket_name}'")
        except ClientError as e:
            print(f"Error setting bucket policy: {e}")
    
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
            print(f"Uploaded: {url}")
            return url
            
        except ClientError as e:
            print(f"Upload error: {e}")
            raise Exception(f"Error uploading to MinIO: {str(e)}")
    
    def delete_image(self, image_url: str) -> bool:
        """
        Удаляет изображение из MinIO по URL
        """
        try:
            key = self.extract_key_from_url(image_url)
            if not key:
                return False
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            print(f"Deleted: {key}")
            return True
            
        except ClientError as e:
            print(f"Delete error: {e}")
            return False
    
    def get_public_url(self, internal_url: str) -> str:
        """
        Преобразует внутренний Docker URL в внешний для браузера
        http://minio:9000/bucket/file.jpg -> http://localhost:9000/bucket/file.jpg
        """
        if internal_url and 'minio:9000' in internal_url:
            return internal_url.replace('minio:9000', 'localhost:9000')
        return internal_url

    def extract_key_from_url(self, image_url: str) -> Optional[str]:
        """Извлекает object key из сохраненного URL."""
        if not image_url:
            return None

        normalized_url = image_url
        if 'minio:9000' in normalized_url:
            normalized_url = normalized_url.replace('minio:9000', 'localhost:9000')

        prefix = f"http://localhost:9000/{self.bucket_name}/"
        if normalized_url.startswith(prefix):
            return normalized_url.replace(prefix, "", 1)

        endpoint_prefix = f"{self.endpoint_url}/{self.bucket_name}/"
        if normalized_url.startswith(endpoint_prefix):
            return normalized_url.replace(endpoint_prefix, "", 1)

        return None
    
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
            print(f"Presigned URL error: {e}")
            return None

    def generate_presigned_url_from_stored_url(self, image_url: str, expiration: int = 3600) -> Optional[str]:
        """Генерирует pre-signed URL на основе URL, сохраненного в БД."""
        key = self.extract_key_from_url(image_url)
        if not key:
            return None
        return self.generate_presigned_url(key, expiration=expiration)

# Глобальный экземпляр сервиса
s3_service = S3Service()
