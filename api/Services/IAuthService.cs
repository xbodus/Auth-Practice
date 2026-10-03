namespace Api.Services;

using Api.Models;


public interface IAuthService
{
    Task<bool> HandleLoginAsync(LoginCredentials credentials);
}