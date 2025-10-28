from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from config import config
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodes the Supabase JWT and extracts user information.
    The token contains all the info we need - no need to call Supabase API.
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            config.SUPABASE_JWT_SECRET, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        
        # Extract user info from the token payload
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            logger.error("Token payload missing 'sub' claim")
            raise credentials_exception
            
        if email is None:
            logger.error("Token payload missing 'email' claim")
            raise credentials_exception
        
        logger.info(f"Successfully authenticated user: {email}")
        
        return {
            "user_id": user_id,
            "email": email
        }
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise credentials_exception