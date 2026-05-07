from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Literal, Optional
from datetime import datetime, timedelta
import os
import logging

# ML Services - опциональны
try:
    from ml_service import glaucoma_service
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    glaucoma_service = None

from database import engine, get_db, Base
from models import User, ProcessedImage
from schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    UpdateUserRoleRequest, UpdateUserStatusRequest, 
    UpdateUserProfileRequest, UserDetailedResponse, UsersStatsResponse,
    UserListResponse, ImageListResponse
)
import crud

from dotenv import load_dotenv
load_dotenv()

from auth import (
    create_access_token,
    get_current_user_from_cookie,
    require_admin,
    require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    generate_refresh_token,
    get_client_info,
    verify_refresh_token
)

# Импорт S3 сервиса
from s3_service import s3_service

# Импорт externe сервисов
from weather_service import weather_service

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
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_upload(file: UploadFile, file_size: int) -> None:
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
        )

    if file_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file is not allowed"
        )

    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10 MB"
        )


def build_image_response(img: ProcessedImage) -> dict:
    original_presigned = s3_service.generate_presigned_url_from_stored_url(img.original_url)
    processed_presigned = s3_service.generate_presigned_url_from_stored_url(img.processed_url) if img.processed_url else None

    return {
        "id": img.id,
        "original_url": original_presigned or "",
        "processed_url": processed_presigned,
        "result": img.result,
        "confidence": calculate_confidence(img.result, img.glaucoma_probability),
        "filename": img.filename,
        "file_size": img.file_size,
        "status": img.status,
        "created_at": img.created_at,
        "processed_at": img.processed_at,
    }


def calculate_confidence(result: str, glaucoma_probability: float) -> float:
    if glaucoma_probability is None:
        return 0.0

    p = max(0.0, min(1.0, float(glaucoma_probability)))
    return max(p, 1.0 - p)

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
    
    #access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username, "user_id": db_user.id},
        expires_delta=access_token_expires
    )
    
    #refresh token
    refresh_token = generate_refresh_token()
    
    device_info, ip_address = get_client_info(request)
    
    #Создаём или обновляем сессию
    crud.create_or_update_session(
        db=db,
        user_id=db_user.id,
        refresh_token=refresh_token,
        device_info=device_info,
        ip_address=ip_address
    )
    
    #Устанавливаем cookies
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

@app.post("/api/token/refresh", response_model=Token, tags=["Authentication"])
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Обновление access token через refresh token
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    session = crud.get_session_by_refresh_token(db, refresh_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user = session.user
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or not found"
        )
    
    device_info, ip_address = get_client_info(request)
    
    try:
        new_refresh_token = generate_refresh_token()
        crud.rotate_refresh_token(db, session.id, new_refresh_token, ip_address)
    except PermissionError as e:
        logger.warning(f"Security alert for user {user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Session security check failed"
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 дней
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/api/users/logout", tags=["Authentication"])
def logout_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
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
    return current_user

@app.get("/api/users", response_model=List[UserResponse], tags=["Users"])
def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Получить список пользователей (только для администраторов)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.delete("/api/users/me", tags=["Users"])
async def delete_current_user(
    current_user: User = Depends(get_current_user_from_cookie),
    response: Response = None,
    db: Session = Depends(get_db)
):
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
        # Читаем файл ОДИН РАЗ в память
        image_bytes = await file.read()
        file_size = len(image_bytes)
        validate_upload(file, file_size)
        
        # Сбрасываем позицию для повторного чтения
        await file.seek(0)
        
        # Загружаем оригинальное изображение в S3 (используем исходный file)
        original_url = s3_service.upload_image(file, current_user.id)
        
        # ML анализ изображения (используем сохраненные байты)
        if ML_AVAILABLE:
            ml_result = glaucoma_service.predict(image_bytes)
            
            result = ml_result['predicted_label']
            glaucoma_probability = ml_result['glaucoma_probability']
            processing_time = ml_result.get('processing_time_ms', 0)
        else:
            # ML недоступна - используем default значения
            result = "unknown"
            glaucoma_probability = 0.0
            processing_time = 0

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
            "original_url": s3_service.generate_presigned_url_from_stored_url(original_url) or "",
            "processed_url": s3_service.generate_presigned_url_from_stored_url(original_url),
            "result": result,
            "confidence": ml_result.get("confidence", calculate_confidence(result, glaucoma_probability)),
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

@app.get("/api/images", response_model=ImageListResponse, tags=["Images"])
async def get_user_images(
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    status_filter: Optional[Literal["pending", "processing", "completed", "failed"]] = Query(None, alias="status"),
    result_filter: Optional[Literal["glaucoma", "non-glaucoma"]] = Query(None, alias="result"),
    sort_by: Literal["created_at", "filename", "file_size", "status"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
):
    """
    Получить список всех обработанных изображений пользователя
    """
    query = db.query(ProcessedImage).filter(ProcessedImage.user_id == current_user.id)

    if search:
        query = query.filter(
            (ProcessedImage.filename.ilike(f"%{search}%")) |
            (ProcessedImage.result.ilike(f"%{search}%"))
        )

    if status_filter:
        query = query.filter(ProcessedImage.status == status_filter)

    if result_filter:
        query = query.filter(ProcessedImage.result == result_filter)

    if date_from:
        query = query.filter(ProcessedImage.created_at >= date_from)

    if date_to:
        query = query.filter(ProcessedImage.created_at <= date_to)

    sort_mapping = {
        "created_at": ProcessedImage.created_at,
        "filename": ProcessedImage.filename,
        "file_size": ProcessedImage.file_size,
        "status": ProcessedImage.status,
    }
    sort_column = sort_mapping[sort_by]
    query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

    total = query.count()
    offset = (page - 1) * page_size
    images = query.offset(offset).limit(page_size).all()

    return {
        "items": [build_image_response(img) for img in images],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

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

    return build_image_response(image)


@app.get("/api/images/{image_id}/download-url", tags=["Images"])
async def get_image_download_url(
    image_id: int,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    image = db.query(ProcessedImage)\
        .filter(ProcessedImage.id == image_id)\
        .filter(ProcessedImage.user_id == current_user.id)\
        .first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    original_url = s3_service.generate_presigned_url_from_stored_url(image.original_url)
    processed_url = s3_service.generate_presigned_url_from_stored_url(image.processed_url) if image.processed_url else None

    if not original_url:
        raise HTTPException(status_code=500, detail="Could not generate secure URL")

    return {
        "original_url": original_url,
        "processed_url": processed_url,
        "expires_in": 3600,
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
        s3_service.delete_image(image.original_url)
        if image.processed_url != image.original_url:
            s3_service.delete_image(image.processed_url)
        
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
        # Чтение содержимого файла
        contents = await file.read()
        validate_upload(file, len(contents))
        await file.seek(0)
        
        # Анализ через ML модель
        if ML_AVAILABLE:
            try:
                prediction = glaucoma_service.predict(contents)
            except Exception as ml_error:
                logger.error(f"ML prediction failed: {ml_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Ошибка ML модели: {str(ml_error)}"
                )
        else:
            # ML недоступна - используем default значения
            prediction = {
                'predicted_label': 'unknown',
                'glaucoma_probability': 0.0,
                'processing_time_ms': 0
            }
        
        # Загрузка в MinIO
        original_url = s3_service.upload_image(file, current_user.id)
        
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
            processing_time_ms=prediction.get('processing_time_ms', 0)
        )
        
        db.add(processed_image)
        db.commit()
        db.refresh(processed_image)
        
        return {
            "id": processed_image.id,
            "original_url": s3_service.generate_presigned_url_from_stored_url(original_url) or "",
            "result": prediction['predicted_label'],
            "confidence": prediction['confidence'],
            "processing_time_ms": prediction.get('processing_time_ms', 0),
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

# ==================== ADMIN ENDPOINTS ====================

@app.get("/api/admin/users", response_model=UserListResponse, tags=["Admin"])
async def admin_get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, max_length=100),
    role: Optional[Literal["user", "admin"]] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: Literal["id", "username", "email", "role", "is_active", "created_at"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей (только администратор)"""
    query = db.query(User)

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )

    if role:
        query = query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    sort_mapping = {
        "id": User.id,
        "username": User.username,
        "email": User.email,
        "role": User.role,
        "is_active": User.is_active,
        "created_at": User.created_at,
    }
    sort_column = sort_mapping[sort_by]
    query = query.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())

    total = query.count()
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    return {
        "items": users,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/admin/users/{user_id}", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/api/admin/users/{user_id}/role", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_role(
    user_id: int,
    role_update: UpdateUserRoleRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """зменить роль пользователя (только администратор)"""
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own role"
        )
    
    updated_user = crud.update_user_role(db, user_id, role_update.role)
    if not updated_user:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    logger.info(f"Admin {current_user.username} changed role of user {user_id} to {role_update.role}")
    return updated_user


@app.patch("/api/admin/users/{user_id}/status", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_status(
    user_id: int,
    status_update: UpdateUserStatusRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own status"
        )

    updated_user = crud.update_user_status(db, user_id, status_update.is_active)
    if not updated_user:
        raise HTTPException(status_code=400, detail="Status update failed")

    return updated_user


@app.put("/api/admin/users/{user_id}", response_model=UserDetailedResponse, tags=["Admin"])
async def admin_update_user_profile(
    user_id: int,
    profile_update: UpdateUserProfileRequest,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        updated_user = crud.update_user_profile(
            db,
            user_id,
            email=profile_update.email,
            username=profile_update.username,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated_user:
        raise HTTPException(status_code=400, detail="Profile update failed")

    return updated_user


@app.delete("/api/admin/users/{user_id}", tags=["Admin"])
async def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    try:
        success = crud.delete_user_by_admin(db, user_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {user_id} deleted successfully"}


@app.get("/api/admin/stats", response_model=UsersStatsResponse, tags=["Admin"])
async def admin_get_system_stats(
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """олучить статистику системы (только администратор)"""
    from models import UserRole
    
    total_users = crud.count_users_by_role(db)
    admin_count = crud.count_users_by_role(db, UserRole.ADMIN.value)
    user_count = crud.count_users_by_role(db, UserRole.USER.value)
    active_users = db.query(User).filter(User.is_active == True).count()
    blocked_users = db.query(User).filter(User.is_active == False).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
        "admin_count": admin_count,
        "user_count": user_count
    }


# ========== EXTERNAL API INTEGRATION ==========

@app.get("/api/weather", tags=["External Data"])
async def get_weather(lat: float, lon: float):
    """
    Получить данные о погоде для координат пользователя
    
    Используется для демонстрации влияния погодных условий на офтальмологические заболевания
    
    Args:
        lat: Широта (latitude)
        lon: Долгота (longitude)
        
    Returns:
        Данные о погоде или ошибка с graceful degradation
        
    Example:
        GET /api/weather?lat=55.7558&lon=37.6173
    """
    if lat is None or lon is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude and longitude are required"
        )
    
    # Валидация координат
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180"
        )
    
    try:
        weather_data = await weather_service.get_weather(lat, lon)
        
        if weather_data:
            return {
                "success": True,
                "data": weather_data,
                "message": "Weather data retrieved successfully"
            }
        else:
            # Graceful degradation - API недоступен, но приложение работает
            return {
                "success": False,
                "data": None,
                "message": "Weather service temporarily unavailable. Application continues to work normally.",
                "fallback": True
            }
    
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        return {
            "success": False,
            "data": None,
            "message": "Error retrieving weather data"
        }


# ========== SEO ENDPOINTS ==========

def get_seo_base_url(request: Request) -> str:
    """Resolve canonical base URL from env var or current request host."""
    configured_base_url = os.getenv("BASE_URL", "").strip()
    if configured_base_url:
        return configured_base_url.rstrip("/")
    return str(request.base_url).rstrip("/")

@app.get("/robots.txt", tags=["SEO"])
async def robots_txt(request: Request):
    """
    Файл robots.txt для управления индексацией поисковыми роботами
    - Разрешает индексацию публичных страниц (/login, /registration, /)
    - Запрещает индексацию защищённых страниц и API эндпоинтов
    """
    base_url = get_seo_base_url(request)

    content = f"""# Robots.txt для AI Ophthalmological Assistant
# Настройки индексации для поисковых роботов

User-agent: *
Allow: /
Allow: /login
Allow: /registration
Allow: /sitemap.xml

# Запрещаем индексацию защищённых страниц
Disallow: /workzone
Disallow: /profile
Disallow: /admin
Disallow: /api/
Disallow: /protected/

# Оптимизация для Googlebot
User-agent: Googlebot
Allow: /
Allow: /login
Allow: /registration
Crawl-delay: 1

# Оптимизация для Bingbot
User-agent: Bingbot
Allow: /
Allow: /login
Allow: /registration
Crawl-delay: 1

# Запрещаем плохим ботам
User-agent: MJ12bot
Disallow: /

User-agent: AhrefsBot
Disallow: /

Sitemap: {base_url}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@app.get("/sitemap.xml", tags=["SEO"])
async def sitemap_xml(request: Request):
    """
    Генерирует sitemap.xml для индексации публичных маршрутов
    Содержит приоритеты: 1.0 для Home, 0.8 для Login/Registration
    """
    base_url = get_seo_base_url(request)
    current_timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    
    urls = [
        {
            "loc": f"{base_url}/",
            "lastmod": current_timestamp,
            "changefreq": "weekly",
            "priority": "1.0"
        },
        {
            "loc": f"{base_url}/login",
            "lastmod": current_timestamp,
            "changefreq": "monthly",
            "priority": "0.8"
        },
        {
            "loc": f"{base_url}/registration",
            "lastmod": current_timestamp,
            "changefreq": "monthly",
            "priority": "0.8"
        }
    ]
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        xml_content += f'''  <url>
    <loc>{url['loc']}</loc>
    <lastmod>{url['lastmod']}</lastmod>
    <changefreq>{url['changefreq']}</changefreq>
    <priority>{url['priority']}</priority>
  </url>
'''
    
    xml_content += '</urlset>'
    
    return Response(content=xml_content, media_type="application/xml")


@app.get("/api/structured-data/organization", tags=["SEO"])
async def get_organization_schema(request: Request):
    """
    Возвращает JSON-LD для Organization
    Используется для улучшения показа в поисковой выдаче Google
    """
    base_url = get_seo_base_url(request)
    
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "AI Ophthalmological Assistant",
        "url": base_url,
        "description": "Онлайн сервис для диагностики заболеваний глаз с использованием искусственного интеллекта",
        "logo": f"{base_url}/logo.png",
        "contact": {
            "@type": "ContactPoint",
            "contactType": "Customer Support",
            "email": "support@example.com"
        },
        "foundingDate": "2024",
        "areaServed": "RU",
        "availableLanguage": ["en", "ru"]
    }


@app.get("/api/structured-data/medical-service", tags=["SEO"])
async def get_medical_service_schema(request: Request):
    """
    Возвращает JSON-LD для MedicalService
    Специфично для медицинских сервисов в поисковой выдаче
    """
    base_url = get_seo_base_url(request)
    
    return {
        "@context": "https://schema.org",
        "@type": "MedicalService",
        "name": "Диагностика глаукомы с помощью ИИ",
        "description": "Использование искусственного интеллекта для точной диагностики глаукомы по снимкам глазного дна",
        "provider": {
            "@type": "Organization",
            "name": "AI Ophthalmological Assistant",
            "url": base_url
        },
        "areaServed": {
            "@type": "Country",
            "name": "Russia"
        },
        "availableLanguage": ["en", "ru"],
        "applicationCategory": "MedicalApplication",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "RUB",
            "description": "Бесплатный сервис диагностики для студентов-врачей"
        }
    }


# ========== Health Check Endpoints ==========

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for Docker containers and load balancers.
    Verifies that the application and database are running.
    Returns 200 if healthy, 503 if unhealthy.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "service": "glaucoma-api",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not healthy"
        )


@app.get("/api/health", tags=["Health"])
async def api_health_check(db: Session = Depends(get_db)):
    """
    Alternative API health check endpoint.
    Returns service status and database connectivity.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "db": "connected",
            "api": "running"
        }
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


# ========== HTTP Status Code Handlers ==========

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Обработчик 404 ошибок"""
    return Response(
        status_code=404,
        content='{"detail": "Страница не найдена", "status": 404}',
        media_type="application/json"
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc: Exception):
    """Обработчик 403 ошибок (доступ запрещён)"""
    return Response(
        status_code=403,
        content='{"detail": "Доступ запрещён", "status": 403}',
        media_type="application/json"
    )
