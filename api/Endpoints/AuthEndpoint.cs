namespace Api.Endpoints;

using Api.Models;
using Api.Services;
using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Http; // Allows access to HttpContext, which gives methods access to HTTP headers and more
using System;



public static class AuthEndpointsExtensions
{
    // Extension method. 'this' keyword before the parameter extends MapAuthEndpoints as if it were a method of app. So we can call app.MapAuthEndpoints to register auth endpoints
    public static void MapAuthEndpoints(this IEndpointRouteBuilder app)
    {
        // Create the endpoint group
        var group = app.MapGroup("/auth").WithTags("Authentication");

        // Register endpoints to the group
        group.MapPost("/login", LoginHandler)
            .RequireRateLimiting("LoginPolicy");
    }

    private static async Task<IResult> LoginHandler(
        LoginCredentials credentials, 
        HttpContext context,
        IAuthService authService)
    {
        // Temporary test login logic
        // Need to confirm if request object is automatically passed like it is in FastAPI
        // Eventually endpoint will need to take data that matches the shape of LoginCredentials and pass to ProcessRequests.HandleLogin()
        var validationResults = new List<ValidationResult>();
        var credentialsContext = new ValidationContext(credentials);

        if (!Validator.TryValidateObject(credentials, credentialsContext, validationResults, validateAllProperties: true))
        {
            var errors = validationResults.Select(r => r.ErrorMessage);
            return Results.BadRequest(new { errors });
        }

        // Call the HandleLogin static method to process the login request
        var isAuthorized = await authService.HandleLoginAsync(credentials);

        if (!isAuthorized)
        {
            return Results.Unauthorized();
        }

        Guid uuid7 = Guid.CreateVersion7();

        var cookies = new CookieOptions
        {
            Expires = DateTimeOffset.UtcNow.AddHours(24) // Expiration time
        };

        context.Response.Cookies.Append("UserSessionId", uuid7.ToString(), cookies);

        return Results.Ok(new { message = $"Hello {credentials.Username}, logged in successfully", response = context.Response.Cookies }); // Placeholder till we can build a proper LoginResponse class
    }
}