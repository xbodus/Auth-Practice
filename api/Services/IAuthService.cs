namespace Verolith.Api.Services;
 
using Verolith.Api.Models;


public interface IAuthService
{
    Task<bool> HandleLoginAsync(LoginCredentials credentials);
    Task<bool> HandleUserSignupAsync(UserSignupRecord user);
}