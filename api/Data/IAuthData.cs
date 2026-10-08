namespace Verolith.Api.Data;

using Verolith.Api.Models;


public interface IAuthData
{
    Task<UserLoginRecord?> GetUserForLoginAsync(string username);
    Task<bool> CreateUserAsync(UserSignupRecord user);
}