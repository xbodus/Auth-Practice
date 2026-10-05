/*
AuthServices.cs

Application logic for completing authentication requests against Postgres database. Will be responsible 
for taking in DTO information and checking it against the database for verification, alterations, etc.
*/
namespace Api.Services;

using Api.Models;


public class AuthService : IAuthService
{
    public async Task<bool> HandleLoginAsync(LoginCredentials credentials)
    {
        // 1. Call Data layer to get password hash
        // 2. Verify password
        // 3. Return success (true) or fail (false)
        return await Task.FromResult(false);
    }
}