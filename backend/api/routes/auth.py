from fastapi import APIRouter, HTTPException, status

from backend.core.security import create_access_token, hash_password, verify_password
from backend.db.supabase_client import get_supabase_client
from backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest):
    supabase = get_supabase_client()
    existing = supabase.table("app_users").select("id").eq("email", payload.email).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    inserted = supabase.table("app_users").insert(
        {
            "email": payload.email,
            "full_name": payload.full_name,
            "password_hash": hash_password(payload.password),
        }
    ).execute()

    user = inserted.data[0]
    token = create_access_token(str(user["id"]))
    return TokenResponse(
        access_token=token,
        user_id=str(user["id"]),
        email=user["email"],
        full_name=user["full_name"],
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    supabase = get_supabase_client()
    res = supabase.table("app_users").select("id,email,full_name,password_hash").eq("email", payload.email).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user = rows[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(str(user["id"]))
    return TokenResponse(
        access_token=token,
        user_id=str(user["id"]),
        email=user["email"],
        full_name=user["full_name"],
    )
