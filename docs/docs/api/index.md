# API Overview
\[Product's\] API is build with ASP .NET Core v10.0.112. The project is organized as follows:

    API  project structure
    api/
    |___Program.cs
    |___appsettings.json
    |___Endpoints/
    |___Services/
    |___Data/
    |___Models/

<br>

---

## Endpoints/
Files that define the API's accessible endpoints are stored in Endpoints/. These endpoints are then grouped by resource and registered to the application within Program.cs, the main application build file.

*Ex: AuthEndpoints.cs registers endpoints for the auth service: auth/login, auth/signup, etc.*

For more information, see [endpoints](endpoints.md)

## Services/
Application logic will be stored as services inside of Services/. Within the project, services will be register to the application in Program.cs as scoped services. Then endpoints will be able to call on the funcationality of these services by declaring the service interface as a dependancy to automatically have the service be injected into the process at time of request. 

*Ex: `public async Task<IResult> LoginHandler(LoginCredentials credentials, IAuthService authService)` can used the functionality of AuthService because IAuthService is declared in the endpoint as authService and has been registered in Program.cs as `builder.Services.AddScoped<IAuthService, AuthService>()`*

For more information, see [services](services.md)

## Data/


## Models/