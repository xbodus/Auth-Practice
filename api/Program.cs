using Verolith.Api.Endpoints;
using Verolith.Api.Services;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.AspNetCore.CookiePolicy;
using Serilog;
using Npgsql;
using Verolith.Api.Data;


// Load .env file into environment variables if it exists. In production we will set proper environment variables
var envPath = Path.Combine(Directory.GetCurrentDirectory(), ".env");
if (File.Exists(envPath))
{
    foreach (var line in File.ReadAllLines(envPath))
    {
        var parts = line.Split('=', 2, StringSplitOptions.TrimEntries);
        if (parts.Length == 2 && !parts[0].StartsWith('#'))
        {
            Environment.SetEnvironmentVariable(parts[0], parts[1]);
        }
    }
}

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();


// Define Middleware
builder.Services.AddCors(options =>
{
    options.AddPolicy("ReactAppPolicy", policy =>
    {
        var allowedHosts = builder.Environment.IsDevelopment() 
            ? ["http://localhost:5137", "http://localhost:3000"]
            : new string[] { };
            
        policy.WithOrigins(allowedHosts)
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});

builder.Services.Configure<CookiePolicyOptions>(options =>
{
    options.HttpOnly = HttpOnlyPolicy.Always;
    options.MinimumSameSitePolicy = SameSiteMode.Strict;
    options.Secure = builder.Environment.IsDevelopment()
        ? CookieSecurePolicy.SameAsRequest
        : CookieSecurePolicy.Always;
});

builder.Services.AddRateLimiter(options =>
{
    options.AddFixedWindowLimiter("LoginPolicy", policy => 
    {
        policy.PermitLimit = 5;
        policy.Window = TimeSpan.FromMinutes(1);
        policy.QueueProcessingOrder = QueueProcessingOrder.OldestFirst;
        policy.QueueLimit = 0;
    });
});

// Configure Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .WriteTo.Console()
    .WriteTo.File("logs/api-.log", rollingInterval: RollingInterval.Day)
    .CreateLogger();

builder.Host.UseSerilog();

// Configure connection to database 
// Core connectionString in appsettings.Development.json (AuthDb)
var baseConnString = builder.Configuration.GetConnectionString("AuthDb");
// Add variables from .env
var connBuilder = new NpgsqlConnectionStringBuilder(baseConnString)
{
    Host = builder.Configuration["PG_HOST"],
    Database = builder.Configuration["PG_DATABASE"],
    Port = builder.Configuration.GetValue<int>("PG_PORT", 5432),
    Username = builder.Configuration["PG_RT_USER"],
    Password = builder.Configuration["PG_RT_PASSWORD"]
};

var dataSource = NpgsqlDataSource.Create(connBuilder.ConnectionString);
// Add database connection to application DI container
builder.Services.AddSingleton(dataSource);

// Add scoped dependencies
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddScoped<IAuthData, AuthData>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

// Log HTTP
app.UseSerilogRequestLogging();

// Register Middleware
app.UseCors("ReactAppPolicy");
app.UseCookiePolicy();
app.UseRateLimiter();

// Register endpoints to application
app.MapAuthEndpoints();


app.Run();