/*
Models.cs 

Stores records and classes for DTOs (Data Transfer Objects)
*/
using System.ComponentModel.DataAnnotations;

namespace Api.Models;


public record LoginCredentials(
    [property: Required(ErrorMessage = "Invalid username/password")] string Username, 
    [property: Required(ErrorMessage = "Invalid username/password")] string Password
);