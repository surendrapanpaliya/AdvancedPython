
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

app = FastAPI(title="Secure Bank API")

# --------------------------
# CONFIG & SETUP
# --------------------------
SECRET_KEY = "supersecretkey"  # Use env variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory databases
users_db: Dict[str, dict] = {}
bank_accounts: Dict[int, dict] = {}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --------------------------
# SCHEMAS
# --------------------------
class User(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class BankAccount(BaseModel):
    id: int
    name: str
    email: EmailStr
    balance: float = Field(..., ge=0)

class TransferRequest(BaseModel):
    from_id: int
    to_id: int
    amount: float = Field(..., gt=0)

# --------------------------
# AUTH FUNCTIONS
# --------------------------
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user(username: str):
    return users_db.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = get_user(username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

# --------------------------
# AUTH ROUTES
# --------------------------
@app.post("/register")
def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = get_password_hash(user.password)
    users_db[user.username] = {"username": user.username, "email": user.email, "hashed_password": hashed}
    return {"message": "User registered successfully"}

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer"}

# --------------------------
# BANK ACCOUNT ROUTES
# --------------------------
@app.post("/accounts/", response_model=BankAccount)
def create_account(account: BankAccount, current_user: dict = Depends(get_current_user)):
    if account.id in bank_accounts:
        raise HTTPException(status_code=400, detail="Account already exists")
    bank_accounts[account.id] = account.model_dump()
    return account

@app.get("/accounts/{account_id}", response_model=BankAccount)
def read_account(account_id: int, current_user: dict = Depends(get_current_user)):
    account = bank_accounts.get(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@app.get("/accounts/", response_model=List[BankAccount])
def list_accounts(current_user: dict = Depends(get_current_user)):
    return list(bank_accounts.values())

@app.post("/transfer/")
def transfer_funds(request: TransferRequest, current_user: dict = Depends(get_current_user)):
    sender = bank_accounts.get(request.from_id)
    receiver = bank_accounts.get(request.to_id)

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or receiver not found")
    if sender["balance"] < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    sender["balance"] -= request.amount
    receiver["balance"] += request.amount

    return {
        "message": f"₹{request.amount} transferred from {sender['name']} to {receiver['name']}",
        "sender_balance": sender["balance"],
        "receiver_balance": receiver["balance"]
    }

# --------------------------
# HOME
# --------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Secure Bank API using JWT!"}
