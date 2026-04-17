from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login(username: str):
    # Заглушка для получения токена/авторизации пользователя
    return {"message": f"User {username} successfully logged in", "token": "dummy_token_123"}
