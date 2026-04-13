---
name: node_express
description: Node.js with Express or NestJS, TypeScript, async patterns
---

# Node.js Backend (Express / NestJS)

TypeScript-based Node APIs using Express (lightweight) or NestJS (opinionated, DI-driven). Use async/await throughout.

## Express + TypeScript

```typescript
// src/server.ts
import express, { Request, Response, NextFunction } from 'express';
import { z } from 'zod';

const app = express();
app.use(express.json());

const CreateUser = z.object({
  email: z.string().email(),
  name: z.string().min(1),
});

app.post('/users', async (req, res, next) => {
  try {
    const data = CreateUser.parse(req.body);
    const user = await userService.create(data);
    res.status(201).json(user);
  } catch (err) { next(err); }
});

app.get('/users/:id', async (req, res, next) => {
  try {
    const user = await userService.get(Number(req.params.id));
    if (!user) return res.status(404).json({ error: 'not found' });
    res.json(user);
  } catch (err) { next(err); }
});

// central error handler
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  if (err instanceof z.ZodError) return res.status(400).json({ errors: err.errors });
  console.error(err);
  res.status(500).json({ error: 'internal' });
});

app.listen(3000);
```

## Async Wrapper Helper

```typescript
type AsyncHandler = (req: Request, res: Response, next: NextFunction) => Promise<unknown>;
const asyncH = (fn: AsyncHandler) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

app.get('/items', asyncH(async (_req, res) => {
  res.json(await itemsService.list());
}));
```

## NestJS Controller + Service

```typescript
// users.module.ts
import { Module } from '@nestjs/common';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';

@Module({ controllers: [UsersController], providers: [UsersService] })
export class UsersModule {}

// users.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';

@Injectable()
export class UsersService {
  private data = new Map<number, { id: number; name: string }>();
  async get(id: number) {
    const u = this.data.get(id);
    if (!u) throw new NotFoundException();
    return u;
  }
  async create(dto: { name: string }) {
    const id = this.data.size + 1;
    const user = { id, ...dto };
    this.data.set(id, user);
    return user;
  }
}

// users.controller.ts
import { Body, Controller, Get, Param, ParseIntPipe, Post } from '@nestjs/common';
import { UsersService } from './users.service';

@Controller('users')
export class UsersController {
  constructor(private readonly svc: UsersService) {}
  @Get(':id') get(@Param('id', ParseIntPipe) id: number) { return this.svc.get(id); }
  @Post()    create(@Body() dto: { name: string })       { return this.svc.create(dto); }
}
```

## Nest Bootstrap with Validation

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
  await app.listen(3000);
}
bootstrap();
```

## Tips
- Always `await` or `.catch()` promises; unhandled rejections crash the process.
- Validate input at the edge (zod for Express, class-validator DTOs for Nest).
- Use `helmet`, `cors`, and rate limiting middleware in production.
- Prefer Nest for larger apps (DI, modules, testing); Express for small services.
