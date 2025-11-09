from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import os
from ml_service import glaucoma_service
from io import BytesIO
import traceback

from ml_service import glaucoma_service

from database import engine, get_db, Base
from models import User, ProcessedImage
from schemas import UserCreate, UserResponse, UserLogin, Token
import crud

from dotenv import load_dotenv
load_dotenv()

from auth import (
    create_access_token,
    get_current_user_from_cookie,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_refresh_token,
    get_client_info
)

# Импорт S3 сервиса
from s3_service import s3_service

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI(
    title="Glaucoma Detection API",
    version="1.0.0",
    description="API для диагностики глаукомы с JWT авторизацией и S3 хранилищем",
    swagger_ui_parameters={"persistAuthorization": True}
)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

@app.get("/", tags=["General"])
def root():
    return {"message": "Glaucoma Detection API is running"}

# ==================== AUTHENTICATION ====================

@app.post(
    "/api/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if user.email:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user(db=db, user=user)

@app.post("/api/users/login", response_model=Token, tags=["Authentication"])
def login_user(
    request: Request,
    response: Response,
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """Авторизация с созданием/обновлением сессии"""
    db_user = crud.get_user_by_username(db, username=user_login.username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not crud.verify_password(user_login.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Создаём access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": db_user.id},
        expires_delta=access_token_expires
    )
    
    # Создаём refresh token
    refresh_token = generate_refresh_token()
    
    # Получаем информацию о клиенте
    device_info, ip_address = get_client_info(request)
    
    # Создаём или обновляем сессию
    crud.create_or_update_session(
        db=db,
        user_id=db_user.id,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address
    )
    
    # Устанавливаем cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 дней
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/api/users/logout", tags=["Authentication"])
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Выход - удаление cookies и отзыв сессии"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        session = crud.get_session_by_refresh_token(db, refresh_token)
        if session:
            crud.revoke_session(db, session.id)
    
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

# ==================== USERS ====================

@app.get("/api/users/me", response_model=UserResponse, tags=["Users"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user_from_cookie)
):
    """Получить текущего пользователя"""
    return current_user

@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Получить список пользователей"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.delete("/api/users/me", tags=["Users"])
async def delete_current_user(
    current_user: User = Depends(get_current_user_from_cookie),
    response: Response = None,
    db: Session = Depends(get_db)
):
    """Удаление текущего пользователя"""
    crud.delete_user(db, current_user.id)
    
    if response:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
    
    return {"message": "User deleted successfully"}

@app.get("/api/users/me/stats", tags=["Users"])
async def get_user_stats(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """Статистика пользователя"""
    stats = crud.get_user_stats(db, current_user.id)
    return stats

# ==================== S3 / IMAGE PROCESSING ====================

@app.post("/api/images/upload", tags=["Images"])
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Загрузка изображения в S3/MinIO для обработки
    """
    try:
        # Проверка типа файла
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Читаем файл ОДИН РАЗ в память
        image_bytes = await file.read()
        file_size = len(image_bytes)
        
        # Сбрасываем позицию для повторного чтения
        await file.seek(0)
        
        # Загружаем оригинальное изображение в S3 (используем исходный file)
        original_url = s3_service.upload_image(file, current_user.id)
        
        # ML анализ изображения (используем сохраненные байты)
        ml_result = glaucoma_service.predict(image_bytes)
        
        result = ml_result['predicted_label']
        glaucoma_probability = ml_result['glaucoma_probability']
        processing_time = ml_result.get('processing_time_ms', 0)

        # Сохраняем информацию в БД
        db_image = ProcessedImage(
            user_id=current_user.id,
            original_url=original_url,
            processed_url=original_url,
            filename=file.filename,
            file_size=file_size,
            result=result,
            glaucoma_probability=glaucoma_probability,
            status="completed",
            processing_time_ms=processing_time
        )

        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        return {
            "id": db_image.id,
            "original_url": original_url,
            "processed_url": original_url,
            "result": result,
            "glaucoma_probability": glaucoma_probability,
            "filename": file.filename,
            "file_size": file_size,
            "created_at": db_image.created_at,
            "status": db_image.status,
            "processing_time_ms": processing_time
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@app.get("/api/images", tags=["Images"])
async def get_user_images(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    Получить список всех обработанных изображений пользователя
    """
    images = db.query(ProcessedImage)\
        .filter(ProcessedImage.user_id == current_user.id)\
        .order_by(ProcessedImage.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return [{
        "id": img.id,
        "original_url": img.original_image_url,
        "processed_url": img.processed_image_url,
        "result": img.result,
        "glaucoma_probability": img.glaucoma_probability,
        "filename": img.filename,
        "file_size": img.file_size,
        "status": img.status,
        "created_at": img.created_at,
        "processed_at": img.processed_at
    } for img in images]

@app.get("/api/images/{image_id}", tags=["Images"])
async def get_image_by_id(
    image_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Получить конкретное изображение по ID
    """
    image = db.query(ProcessedImage)\
        .filter(ProcessedImage.id == image_id)\
        .filter(ProcessedImage.user_id == current_user.id)\
        .first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return {
        "id": image.id,
        "original_url": image.original_image_url,
        "processed_url": image.processed_image_url,
        "result": image.result,
        "glaucoma_probability": image.glaucoma_probability,
        "filename": image.filename,
        "file_size": image.file_size,
        "status": image.status,
        "created_at": image.created_at,
        "processed_at": image.processed_at
    }

@app.delete("/api/images/{image_id}", tags=["Images"])
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Удалить изображение из S3 и БД
    """
    image = db.query(ProcessedImage)\
        .filter(ProcessedImage.id == image_id)\
        .filter(ProcessedImage.user_id == current_user.id)\
        .first()
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        # Удаляем из S3
        s3_service.delete_image(image.original_image_url)
        if image.processed_image_url != image.original_image_url:
            s3_service.delete_image(image.processed_image_url)
        
        # Удаляем из БД
        db.delete(image)
        db.commit()
        
        return {"message": "Image deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")

# ==================== CHECKS (старые эндпоинты) ====================

@app.get("/api/users/me/checks", tags=["Checks"])
async def get_user_checks(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Получить все проверки текущего пользователя"""
    checks = crud.get_user_checks(db, current_user.id, skip, limit)
    return checks

@app.post("/api/images/analyze", status_code=status.HTTP_200_OK)
async def analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie)
):
    """
    Загрузка и анализ изображения на глаукому
    """
    try:
        # Проверка типа файла
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл должен быть изображением"
            )
        
        # Чтение содержимого файла
        contents = await file.read()
        
        # Анализ через ML модель
        try:
            prediction = glaucoma_service.predict(contents)
        except Exception as ml_error:
            logger.error(f"ML prediction failed: {ml_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка ML модели: {str(ml_error)}"
            )
        
        # Загрузка в MinIO
        original_url = s3_service.upload_file(
            file_data=contents,
            filename=file.filename,
            user_id=current_user.id,
            file_type='original'
        )
        
        # Сохранение результата в БД
        processed_image = ProcessedImage(
            user_id=current_user.id,
            original_url=original_url,
            processed_url=original_url,
            filename=file.filename,
            file_size=len(contents),
            result=prediction['predicted_label'],
            glaucoma_probability=prediction['glaucoma_probability'],
            status='completed',
            processing_time_ms=prediction['processing_time_ms']
        )
        
        db.add(processed_image)
        db.commit()
        db.refresh(processed_image)
        
        return {
            "id": processed_image.id,
            "original_url": original_url,
            "result": prediction['predicted_label'],
            "glaucoma_probability": prediction['glaucoma_probability'],
            "confidence": prediction['confidence'],
            "processing_time_ms": prediction['processing_time_ms'],
            "all_probabilities": prediction['all_probabilities']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Неожиданная ошибка: {str(e)}"
        )