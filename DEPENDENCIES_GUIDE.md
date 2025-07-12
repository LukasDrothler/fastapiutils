# FastAPI Utils - Dependency Injection Guide

This guide will walk you through the dependency injection system in FastAPI Utils step by step, explaining what happens and why.

## Overview

The dependency injection system in `dependencies.py` is designed to manage service instances (like database connections, authentication, email services, etc.) in a clean and organized way. It follows the **Dependency Injection** pattern, which helps with:

- **Separation of concerns**: Each service has a single responsibility
- **Testability**: Easy to mock services for testing
- **Configuration management**: Services are configured in one place
- **Lazy loading**: Services are only created when needed

## Step-by-Step Breakdown

### Step 1: The DependencyContainer Class

```python
class DependencyContainer:
    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
```

**What it does:**
- Creates a container that holds different types of service registrations
- `_factories`: Functions that know how to create service instances
- `_singletons`: Already-created service instances (created once, reused)

**Why it matters:**
This is the central registry where all your services are managed. Think of it as a phone book for services.

### Step 2: Service Registration Methods

#### register_singleton()
```python
def register_singleton(self, service_name: str, instance: Any) -> None:
    self._singletons[service_name] = instance
```
**What it does:** Stores an already-created service instance
**When to use:** When you have a service instance ready to go

#### register_factory()
```python
def register_factory(self, service_name: str, factory: Callable) -> None:
    self._factories[service_name] = factory
```
**What it does:** Stores a function that can create a service when needed
**When to use:** When you want the service to be created only when first requested

### Step 3: Service Retrieval

```python
def get(self, service_name: str) -> Any:
    # Check if it's a singleton first
    if service_name in self._singletons:
        return self._singletons[service_name]
        
    # Check if there's a factory for it
    if service_name in self._factories:
        instance = self._factories[service_name]()
        # Cache as singleton after first creation
        self._singletons[service_name] = instance
        return instance
        
    raise ValueError(f"Service '{service_name}' not found in container")
```

**What happens when you request a service:**
1. **First check**: Is there already a created instance? If yes, return it
2. **Second check**: Is there a factory function? If yes, call it to create the instance
3. **Cache the result**: Store the newly created instance as a singleton for future use
4. **Error handling**: If neither exists, throw an error

**Why this pattern:** This implements "lazy singleton" - services are created only when first needed, but then reused.

### Step 4: Factory Functions

These are the functions that know how to create each type of service:

#### Database Service Factory
```python
def create_database_service() -> DatabaseService:
    return DatabaseService()
```
**What it does:** Creates a new database service instance
**Note:** Simple creation, no special configuration

#### Mail Service Factory
```python
def create_mail_service() -> MailService:
    return MailService()
```
**What it does:** Creates a mail service instance
**Note:** Mail service is now required for email verification functionality. This will raise an error if SMTP configuration is missing.

#### I18n Service Factory
```python
def create_i18n_service(custom_locales_dir: Optional[str] = None, default_locale: str = "en") -> I18nService:
    return I18nService(custom_locales_dir=custom_locales_dir, default_locale=default_locale)
```
**What it does:** Creates an internationalization service with custom configuration
**Parameters:** Allows customization of language files location and default language

#### Auth Service Factory
```python
def create_auth_service(
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 30,
    token_url: str = "token",
    private_key_filename: str = "private_key.pem",
    public_key_filename: str = "public_key.pem"
):
    from .auth_service import AuthService
    return AuthService(...)
```
**What it does:** Creates an authentication service with JWT token configuration
**Import note:** Imports AuthService inside the function to avoid circular imports

### Step 5: Setup Function

```python
def setup_dependencies(...):
    container.clear()
    
    # Register factory functions
    container.register_factory("database_service", create_database_service)
    container.register_factory("mail_service", create_mail_service)
    container.register_factory("i18n_service", 
                              lambda: create_i18n_service(custom_locales_dir, default_locale))
    
    # Special factory for auth service
    def auth_service_factory():
        return create_auth_service(...)
    
    container.register_factory("auth_service", auth_service_factory)
```

**What happens:**
1. **Clear existing**: Remove any previously registered services
2. **Register factories**: Tell the container how to create each service
3. **Parameter binding**: Use lambda functions and closures to "bake in" configuration parameters

**Why lambdas and closures:** This allows the setup function to pass configuration parameters to the factory functions without the container needing to know about them.

### Step 6: FastAPI Dependency Functions

These functions integrate with FastAPI's dependency injection system:

```python
@lru_cache()
def get_auth_service():
    return container.get("auth_service")
```

**What @lru_cache() does:**
- Caches the result of the function call
- On first call: `container.get("auth_service")` is executed
- On subsequent calls: Returns cached result without calling container.get()

**Why this matters:** FastAPI calls dependency functions on every request. Without caching, you'd create new service instances for every request, which is inefficient.

### Step 7: OAuth2 and User Dependencies

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    i18n_service: I18nService = Depends(get_i18n_service)
) -> UserInDB:
    return auth_service.get_current_user(token, db_service=db_service, i18n_service=i18n_service)
```

**What happens in a request:**
1. **Extract token**: `oauth2_scheme` extracts the JWT token from the Authorization header
2. **Get services**: FastAPI resolves the auth, database, and i18n services through dependency injection
3. **Validate user**: `auth_service.get_current_user()` validates the token and returns user information

### Step 8: Convenience Type Annotations

```python
CurrentUser = Annotated[UserInDB, Depends(get_current_user)]
CurrentActiveUser = Annotated[UserInDB, Depends(get_current_active_user)]
```

**What these do:** Provide shorthand type annotations for route handlers
**Usage example:**
```python
@app.get("/profile")
def get_profile(user: CurrentUser):
    return {"username": user.username}
```

## Complete Flow Example

Let's trace what happens when a user makes an authenticated request:

### 1. Application Startup
```python
# In your main.py or similar
setup_dependencies(
    default_locale="en",
    access_token_expire_minutes=60
)
```

### 2. First Authenticated Request

**Step 2a:** FastAPI sees that the route requires a `CurrentUser`
```python
@app.get("/profile")
def get_profile(user: CurrentUser):
    pass
```

**Step 2b:** FastAPI resolves `CurrentUser` → `Depends(get_current_user)`

**Step 2c:** `get_current_user` needs several dependencies:
- `token` from `oauth2_scheme` (extracts from Authorization header)
- `auth_service` from `get_auth_service()`
- `db_service` from `get_database_service()`
- `i18n_service` from `get_i18n_service()`

**Step 2d:** Each service dependency is resolved:
1. `get_auth_service()` → `container.get("auth_service")` → calls factory → creates AuthService instance → caches it
2. `get_database_service()` → `container.get("database_service")` → calls factory → creates DatabaseService instance → caches it
3. `get_i18n_service()` → `container.get("i18n_service")` → calls factory → creates I18nService instance → caches it

**Step 2e:** `get_current_user()` is called with all dependencies and returns a UserInDB object

### 3. Subsequent Requests

**What's different:** All the `@lru_cache()` decorated functions return cached service instances, so no new services are created.

## Benefits of This Approach

1. **Performance**: Services are created once and reused
2. **Configuration**: All service configuration happens in one place (`setup_dependencies`)
3. **Testing**: Easy to replace services with mocks
4. **Flexibility**: Can easily swap service implementations
5. **Clean Code**: Route handlers only need to declare what they need

## Common Patterns

## Common Patterns

### Using in Route Handlers
```python
from fastapi import Depends
from fastapiutils import CurrentActiveUser
from fastapiutils.dependencies import get_mail_service
from fastapiutils.mail_service import MailService

@app.get("/send-email")
def send_email(
    mail_service: MailService = Depends(get_mail_service),
    user: CurrentActiveUser
):
    if mail_service:
        mail_service.send_email(user.email, "Hello!")
    return {"status": "sent"}

@app.post("/user/register")
def create_user(
    user_data: CreateUser,
    auth_service: AuthService = Depends(get_auth_service),
    db_service: DatabaseService = Depends(get_database_service),
    mail_service: MailService = Depends(get_mail_service),
    i18n_service: I18nService = Depends(get_i18n_service),
):
    return auth_service.register_new_user(
        user_data, "en", 
        db_service=db_service, 
        i18n_service=i18n_service
        )
```

### Testing with Mocks
```python
def test_my_route():
    # Override dependencies for testing
    app.dependency_overrides[get_database_service] = lambda: MockDatabaseService()
    
    # Your test code here
```

This dependency injection system provides a robust foundation for managing services in your FastAPI application while keeping the code clean, testable, and maintainable.
