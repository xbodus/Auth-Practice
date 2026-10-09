/*
AuthServices.cs

Application logic for completing authentication requests against Postgres database. Will be responsible 
for taking in DTO information and checking it against the database for verification, alterations, etc.
*/
namespace Verolith.Api.Services;

using Verolith.Api.Data;
using Verolith.Api.Models;
using BCrypt.Net;


public class AuthService(ILogger<AuthService> logger, IAuthData authData) : IAuthService
{

    public async Task<bool> HandleLoginAsync(LoginCredentials credentials)
    {
        // 1. Call Data layer to get password hash
        // 2. Verify password
        // 3. Return success (true) or fail (false)
        UserLoginRecord? loginRecord = await authData.GetUserForLoginAsync(credentials.Username);

        if (loginRecord is null)
        {
            logger.LogWarning("Failed login request from {username}", credentials.Username);
            return false;
        }

        // Validate password hash
        logger.LogInformation("Successful login request from {username}", credentials.Username);
        return true;
    }

    public async Task<bool> HandleUserSignupAsync(UserSignupRecord user)
    {
        // Handles user signup
        // Hash and salt user password
        string passwordHash =  BCrypt.HashPassword(user.Password);

        bool result = await authData.CreateUserAsync(user with {Password = passwordHash});

        if (!result)
        {
            logger.LogWarning("Failed to create user for {username}", user.Username);
            // NOTE: Insert some retry logic incase database is overloaded. Backoff and try again 3 times
            return false;
        }

        logger.LogInformation("Successfully created user for {username}", user.Username);
        return true;
    }
}