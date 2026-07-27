
- `main.go`: 
    
    This file usually contains the entry point of the application, including the initialization of the Gin router and the starting of the server.
    
- `config/`: 
    
    Stores configuration files (e.g., database connection strings, API keys, environment-specific settings). Tools like Viper can be used for managing configuration.
    
- `models/` (or `domain/`): 
    
    Defines the data structures (structs) that represent your application's entities and potentially database models (if using an ORM like GORM).
    
- `handlers/` (or `controllers/`): 
    
    Contains the functions that handle incoming HTTP requests, process them, and send responses. These handlers interact with the service layer.
    
- `services/` (or `usecases/`): 
    
    Encapsulates the core business logic of your application. This layer orchestrates interactions between handlers and repositories, performing operations on your data.
    
- `repositories/` (or `dao/`): 
    
    Handles data persistence logic, abstracting away the details of interacting with a database (e.g., SQL, NoSQL). This layer is responsible for CRUD operations.
    
- `routes/`: 
    
    Defines the application's API endpoints and maps them to the corresponding handlers. This can be done in a separate file or within `main.go` for smaller projects.
    
- `utils/`: 
    
    Contains utility functions and helper methods that are used across different parts of the application (e.g., error handling, logging, common data transformations).
    
- `middleware/`: 
    
    Houses custom Gin middleware functions for tasks like authentication, authorization, logging, or request validation.
    
- `tests/`: 
    
    Contains unit and integration tests for your application's components.

```shell
.  
├── main.go  
├── config/  
│ └── config.go  
├── models/  
│ └── user.go  
├── handlers/  
│ └── user_handler.go  
├── services/  
│ └── user_service.go  
├── repositories/  
│ └── user_repository.go  
├── routes/  
│ └── routes.go  
├── utils/  
│ └── error_handler.go  
├── middleware/  
│ └── auth_middleware.go  
└── tests/  
└── user_test.go
```

entity = 数据库模型（ORM）
dto = 接收 API 输入
vo = API 输出

View Object (VO)