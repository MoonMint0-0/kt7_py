from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import TokenResponse, UserRegister, UserResponse, UserRoleUpdate

limiter = Limiter(key_func=get_remote_address)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
users_router = APIRouter(prefix="/users", tags=["Users"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    return service.register_user(db, payload)


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    token = service.authenticate_user(db, email=form_data.username, password=form_data.password)
    return TokenResponse(access_token=token)


@users_router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@users_router.get("/", response_model=list[UserResponse])
def read_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return service.list_users(db)


@users_router.patch("/{user_id}/role", response_model=UserResponse)
def change_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return service.update_user_role(db, user_id=user_id, role=payload.role)