# ER-диаграмма проекта CarSales

```mermaid
erDiagram
    User {
        int id PK
        string username
        string email
        string first_name
        string last_name
        boolean is_staff
        boolean is_active
        datetime date_joined
    }
    
    Profile {
        int id PK
        int user_id FK
        string phone_num
    }
    
    GoogleOAuthProfile {
        int id PK
        int user_id FK
        string google_user_id
        text access_token
        text refresh_token
        datetime token_expiry
        datetime created_at
        datetime updated_at
    }
    
    Brand {
        int id PK
        string name
    }
    
    BodyType {
        int id PK
        string name
    }
    
    EngineType {
        int id PK
        string name
    }
    
    Color {
        int id PK
        string name
    }
    
    SellStatus {
        int id PK
        string name
    }
    
    Region {
        int id PK
        string name
    }
    
    Auto {
        int id PK
        int brand_id FK
        text description
        string model
        int year
        int mileage
        decimal price
        int body_type_id FK
        int engine_type_id FK
        int color_id FK
        int region_id FK
        int sell_status_id FK
        int views
        int profile_id FK
        datetime created_at
        datetime updated_at
    }
    
    Photo {
        int id PK
        string url
        text description
    }
    
    AutoPhoto {
        int id PK
        int auto_id FK
        int photo_id FK
    }
    
    Favorite {
        int id PK
        int user_id FK
        int auto_id FK
        datetime created_at
    }
    
    Review {
        int id PK
        int auto_id FK
        int user_id FK
        int rating
        text text
        datetime created_at
        datetime updated_at
    }
    
    ContactMessage {
        int id PK
        string name
        string email
        text message
        string attachment
        datetime created_at
    }
    
    %% Связи
    User ||--|| Profile : "has"
    Profile ||--o{ GoogleOAuthProfile : "has"
    User ||--o{ Auto : "creates"
    User ||--o{ Favorite : "adds"
    User ||--o{ Review : "writes"
    User ||--o{ ContactMessage : "sends"
    
    Brand ||--o{ Auto : "has"
    BodyType ||--o{ Auto : "has"
    EngineType ||--o{ Auto : "has"
    Color ||--o{ Auto : "has"
    Region ||--o{ Auto : "located_in"
    SellStatus ||--o{ Auto : "has"
    
    Auto ||--o{ AutoPhoto : "has"
    Photo ||--o{ AutoPhoto : "belongs_to"
    Auto ||--o{ Review : "receives"
```

## Описание связей:

1. **User ↔ Profile**: Один к одному - каждый пользователь имеет один профиль
2. **Profile → GoogleOAuthProfile**: Один ко многим - профиль может иметь несколько OAuth-профилей
3. **User → Auto**: Один ко многим - пользователь может создать несколько объявлений
4. **User → Favorite**: Один ко многим - пользователь может добавить несколько автомобилей в избранное
5. **User → Review**: Один ко многим - пользователь может оставить несколько отзывов
6. **User → ContactMessage**: Один ко многим - пользователь может отправить несколько сообщений

7. **Brand → Auto**: Один ко многим - одна марка может быть у многих автомобилей
8. **BodyType → Auto**: Один ко многим - один тип кузова может быть у многих автомобилей
9. **EngineType → Auto**: Один ко многим - один тип двигателя может быть у многих автомобилей
10. **Color → Auto**: Один ко многим - один цвет может быть у многих автомобилей
11. **Region → Auto**: Один ко многим - один регион может содержать много автомобилей
12. **SellStatus → Auto**: Один ко многим - один статус может быть у многих автомобилей

13. **Auto ↔ AutoPhoto ↔ Photo**: Многие ко многим через промежуточную таблицу
14. **Auto → Review**: Один ко многим - один автомобиль может иметь много отзывов

## Особенности:
- **AutoPhoto** - промежуточная таблица для связи M2M между Auto и Photo
- **Favorite** - уникальное ограничение на пару (user, auto)
- **Review** - уникальное ограничение на пару (user, auto)
- **Auto** наследует от TimeStamped (created_at, updated_at)
- **Auto** имеет кастомный менеджер AutoManager с методом available()
- **Auto** имеет метод is_premium() для определения премиум-автомобилей 