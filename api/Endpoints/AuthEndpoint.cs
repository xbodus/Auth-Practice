namespace Api.Endpoints;

using Api.Models;
using Api.Services;
using System.ComponentModel.DataAnnotations;



public static class AuthEndpoints
{
    public static void MapAuthEndpoints(this IEndpointRouteBuilder app)
    {
        // Create the endpoint group
        var group = app.MapGroup("/auth").WithTags("Authentication");

        // Register endpoints to the group
        group.MapPost("/login", LoginHandler);
    }

    private static async Task<IResult> LoginHandler(LoginCredentials credentials)
    {
        // Temporary test login logic
        // Need to confirm if request object is automatically passed like it is in FastAPI
        // Eventually endpoint will need to take data that matches the shape of LoginCredentials and pass to ProcessRequests.HandleLogin()
        var validationResults = new List<ValidationResult>();
        var context = new ValidationContext(credentials);

        if (!Validator.TryValidateObject(credentials, context, validationResults, validateAllProperties: true))
        {
            var errors = validationResults.Select(r => r.ErrorMessage);
            return Results.BadRequest(new { errors });
        }

        return Results.Ok(new { message = $"Hello {credentials.Username}, logged in successfully" }); // Placeholder till we can build a proper LoginResponse class
    }
}