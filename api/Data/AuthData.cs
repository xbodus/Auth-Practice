namespace Verolith.Api.Data;

using Npgsql;
using Dapper;
using Verolith.Api.Models;
using Microsoft.AspNetCore.Razor.TagHelpers;

public class AuthData(NpgsqlDataSource dataSource) : IAuthData
{
    public async Task<UserLoginRecord?> GetUserForLoginAsync(string username)
    {
        // Returns query results from get_user_for_login()

        // SQL query 
        // maps database values user_id, password_hash to UserLoginRecord values UserId, PasswordHash respectively
        const string sql = "SELECT user_id AS UserId, password_hash AS PasswordHash FROM get_user_for_login(@Username)";

        // Opens available connection from available connection pool created in Program.cs
        await using var connection = await dataSource.OpenConnectionAsync();

        // Queries using get_user_for_login(username)
        // When finished, returns the connection back to pool
        return await connection.QuerySingleOrDefaultAsync<UserLoginRecord>(
            sql,
            new { Username = username }
        );
    }

    public async Task<bool> CreateUserAsync(UserSignupRecord user)
    {
        // Returns success of fail for inserting user into users table

        // SQL query
        const string sql = """
                INSERT INTO users (first_name, last_name, username, password, email, phone, dob, address, city, state, zipcode, country, company)
                VALUES (@FirstName, @LastName, @Username, @Password, @Email, @Phone, @DOB, @Address, @City, @State, @Zipcode, @Country, @Company)
            """;
        
        await using var connection = await dataSource.OpenConnectionAsync();

        int affectedRows = await connection.ExecuteAsync(sql, user);

        return affectedRows > 0;
    }
}