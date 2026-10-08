namespace Verolith.Api.Endpoints;

using Verolith.Api.Models;
using Verolith.Api.Services;
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
        group.MapPost("/signup", SignupHandler);
    }

    private static async Task<IResult> LoginHandler(
        LoginCredentials credentials, 
        IAuthService authService)
    {
        // Temporary test login logic
        var validationResults = new List<ValidationResult>();
        var credentialsContext = new ValidationContext(credentials);

        if (!Validator.TryValidateObject(credentials, credentialsContext, validationResults, validateAllProperties: true))
        {
            var errors = validationResults.Select(r => r.ErrorMessage);
            return Results.BadRequest(new { errors });
        }

        var isAuthorized = await authService.HandleLoginAsync(credentials);

        if (!isAuthorized)
        {
            return Results.Unauthorized();
        }

        return Results.Ok(new { message = $"Hello {credentials.Username}, logged in successfully" }); // Placeholder till we can build a proper LoginResponse class
    }

    private static async Task<IResult> SignupHandler(
        UserSignupRecord user,
        IAuthService authService
    )
    {
        // Validate user input matches required input shape
        var validationResults = new List<ValidationResult>();
        var userContext = new ValidationContext(user);

        if (!Validator.TryValidateObject(user, userContext, validationResults, validateAllProperties: true))
        {
            var errors = validationResults.Select(r => r.ErrorMessage);
            return Results.BadRequest(new { errors }); // Return 400 malformed payload
        }

        bool result = await authService.HandleUserSignupAsync(user); 

        if (!result)
        {
            return Results.InternalServerError(); // Return 500 server side error
        }

        return Results.Created(); // Return 201 Created
    }
}