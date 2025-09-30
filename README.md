# 🛡️ User Authentication Service (Group 4)

This service handles **user authentication and authorization** for our project.  
It integrates **Auth0** for access tokens and uses **Django** to manage refresh tokens, user persistence, and token validation.

---

## ⚙️ Tech Stack
- **Django 5**  
- **Django REST Framework**  
- **Auth0** (Access token provider)  
- **SimpleJWT** (Refresh token management)  
- **PostgreSQL** (User storage)  

---

## 🔑 Authentication Flow

1. **User Login**  
   - User logs in with email & password.  
   - Django authenticates locally.  
   - Service requests **access token** from Auth0.  
   - Django issues a **refresh token**.  
   - Response contains both tokens + user details.

2. **Access Token**  
   - Issued by **Auth0**.  
   - Short-lived (default 5 min).  
   - Used for **authorization** in requests.  

3. **Refresh Token**  
   - Issued & managed by **Django**.  
   - Used to request a new **Auth0 access token** via `/api/users/refresh-token/`.

4. **Verify & Validate**  
   - Other services can call `/verify-token/` and `/validate-token/` to confirm token validity and retrieve user details.

---

## 📌 API Endpoints

Base URL:  http://localhost:8000/api/users/
