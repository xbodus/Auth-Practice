/*
AuthServices.cs

Application logic for completing authentication requests against Postgres database. Will be responsible 
for taking in DTO information and checking it against the database for verification, alterations, etc.
*/
namespace Api.Services;

using Api.Models;


public class ProcessRequest
{
    public static async Task<IResult> HandleLogin(LoginCredentials credentials)
    {
        // 1. Call Data layer to get password hash
        // 2. Verify password
        // 3. Return IResult (Ok, Unauthorized, etc.)
        return Results.Ok(new { Message = "Logged in successfully" });
    }
}