---
name: dotnet
description: ASP.NET Core with DI, Entity Framework, minimal APIs or controllers, MediatR
---

# ASP.NET Core

Modern .NET (8+) with dependency injection, EF Core, minimal APIs or controllers, and optional MediatR for CQRS.

## Program.cs (Minimal API)

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<AppDbContext>(opt =>
    opt.UseNpgsql(builder.Configuration.GetConnectionString("Default")));
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<Program>());
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();
app.UseSwagger(); app.UseSwaggerUI();

app.MapGet("/users/{id:int}", async (int id, IMediator m) =>
{
    var user = await m.Send(new GetUserQuery(id));
    return user is null ? Results.NotFound() : Results.Ok(user);
});

app.MapPost("/users", async (CreateUserCommand cmd, IMediator m) =>
    Results.Created($"/users/{await m.Send(cmd)}", null));

app.Run();
```

## EF Core DbContext & Entity

```csharp
public class User
{
    public int Id { get; set; }
    public string Email { get; set; } = default!;
    public string Name { get; set; } = default!;
}

public class AppDbContext(DbContextOptions<AppDbContext> opts) : DbContext(opts)
{
    public DbSet<User> Users => Set<User>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<User>().HasIndex(u => u.Email).IsUnique();
    }
}
```

## MediatR Handler (CQRS)

```csharp
public record GetUserQuery(int Id) : IRequest<UserDto?>;
public record UserDto(int Id, string Name, string Email);

public class GetUserHandler(AppDbContext db) : IRequestHandler<GetUserQuery, UserDto?>
{
    public async Task<UserDto?> Handle(GetUserQuery q, CancellationToken ct)
    {
        var u = await db.Users.FindAsync([q.Id], ct);
        return u is null ? null : new UserDto(u.Id, u.Name, u.Email);
    }
}
```

## Controller Alternative

```csharp
[ApiController]
[Route("api/[controller]")]
public class UsersController(IMediator mediator) : ControllerBase
{
    [HttpGet("{id:int}")]
    public async Task<ActionResult<UserDto>> Get(int id)
    {
        var user = await mediator.Send(new GetUserQuery(id));
        return user is null ? NotFound() : Ok(user);
    }
}
```

## Tips
- Use primary constructors (C# 12) for DI: `public class Svc(IDep dep)`.
- Register services with correct lifetime: `AddScoped` for EF contexts, `AddSingleton` for stateless.
- Use `IResult` with `Results.Ok/NotFound/Problem` in minimal APIs.
- Apply migrations: `dotnet ef migrations add Init && dotnet ef database update`.
- Validate inputs via FluentValidation or data annotations; return `ValidationProblem`.
