---
name: database_design
description: Design JPA entities, relationships, database migrations with Flyway or Liquibase, indexing strategies, and repository patterns for Spring Boot applications
---

# Database Design Skill

## Overview
This skill covers how to design and manage the persistence layer of a Spring Boot application using JPA/Hibernate, including entity modeling, relationships, migration management, indexing, and advanced repository patterns.

## JPA Entity Fundamentals

### Base Entity

Create an abstract base entity for shared audit fields:

```java
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
public abstract class BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Version
    private Long version;  // Optimistic locking
}
```

Enable JPA auditing in your configuration:

```java
@Configuration
@EnableJpaAuditing
public class JpaConfig {
}
```

### Entity Example

```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_user_email", columnList = "email", unique = true),
    @Index(name = "idx_user_active_role", columnList = "active, role")
})
@Getter
@Setter
@NoArgsConstructor
public class User extends BaseEntity {

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(nullable = false)
    private String password;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private UserRole role;

    @Column(nullable = false)
    private boolean active = true;

    @OneToMany(mappedBy = "author", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Post> posts = new ArrayList<>();

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "user_tags",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "tag_id")
    )
    private Set<Tag> tags = new HashSet<>();

    // Helper methods for bidirectional relationships
    public void addPost(Post post) {
        posts.add(post);
        post.setAuthor(this);
    }

    public void removePost(Post post) {
        posts.remove(post);
        post.setAuthor(null);
    }
}
```

## Relationships

### One-to-Many / Many-to-One

```java
@Entity
@Table(name = "posts")
@Getter
@Setter
@NoArgsConstructor
public class Post extends BaseEntity {

    @Column(nullable = false, length = 200)
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private PostStatus status = PostStatus.DRAFT;

    // Many posts belong to one user
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "author_id", nullable = false)
    private User author;

    // One post has many comments
    @OneToMany(mappedBy = "post", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("createdAt DESC")
    private List<Comment> comments = new ArrayList<>();
}
```

### Many-to-Many with Extra Columns

When a join table needs additional columns, model it as an entity:

```java
@Entity
@Table(name = "enrollments")
@Getter
@Setter
@NoArgsConstructor
public class Enrollment extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "student_id", nullable = false)
    private User student;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "course_id", nullable = false)
    private Course course;

    @Column(nullable = false)
    private LocalDate enrolledAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private EnrollmentStatus status;

    private Double grade;
}
```

### One-to-One

```java
@Entity
@Table(name = "user_profiles")
@Getter
@Setter
@NoArgsConstructor
public class UserProfile extends BaseEntity {

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    @Column(length = 500)
    private String bio;

    private String avatarUrl;

    private LocalDate birthDate;
}
```

## Key Relationship Rules

1. Always use `FetchType.LAZY` on `@ManyToOne` and `@OneToOne` to avoid N+1 queries. `@OneToMany` and `@ManyToMany` are lazy by default.
2. Put `cascade = CascadeType.ALL` and `orphanRemoval = true` only on the owning parent side.
3. Always use helper methods (`addPost`, `removePost`) to keep both sides of bidirectional relationships in sync.
4. Use `@OrderBy` on collections when order matters.
5. Never use `CascadeType.ALL` on `@ManyToOne` -- it would cascade deletes to the parent.

## Database Migrations with Flyway

### Setup

Add to `pom.xml`:

```xml
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

Configure in `application.yml`:

```yaml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
  jpa:
    hibernate:
      ddl-auto: validate   # Flyway manages the schema, Hibernate only validates
```

### Migration File Naming

Place SQL files in `src/main/resources/db/migration/`:

```
db/migration/
  V1__create_users_table.sql
  V2__create_posts_table.sql
  V3__create_comments_table.sql
  V4__add_user_profile.sql
  V5__add_index_on_posts_status.sql
```

Naming convention: `V{version}__{description}.sql` (two underscores between version and description).

### Migration Examples

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(20)  NOT NULL DEFAULT 'USER',
    active      BOOLEAN      NOT NULL DEFAULT TRUE,
    version     BIGINT       NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP
);

CREATE UNIQUE INDEX idx_user_email ON users (email);
CREATE INDEX idx_user_active_role ON users (active, role);
```

```sql
-- V2__create_posts_table.sql
CREATE TABLE posts (
    id          BIGSERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    content     TEXT,
    status      VARCHAR(20)  NOT NULL DEFAULT 'DRAFT',
    author_id   BIGINT       NOT NULL REFERENCES users(id),
    version     BIGINT       NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP
);

CREATE INDEX idx_post_author ON posts (author_id);
CREATE INDEX idx_post_status ON posts (status);
CREATE INDEX idx_post_created ON posts (created_at DESC);
```

```sql
-- V4__add_user_profile.sql
CREATE TABLE user_profiles (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT       NOT NULL UNIQUE REFERENCES users(id),
    bio         VARCHAR(500),
    avatar_url  VARCHAR(500),
    birth_date  DATE,
    version     BIGINT       NOT NULL DEFAULT 0,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP
);
```

### Adding Columns Safely

```sql
-- V5__add_phone_to_users.sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
-- No NOT NULL without a default on existing tables with data
```

## Database Migrations with Liquibase (Alternative)

If using Liquibase instead of Flyway:

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.liquibase</groupId>
    <artifactId>liquibase-core</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.yaml
```

```yaml
# db/changelog/db.changelog-master.yaml
databaseChangeLog:
  - include:
      file: db/changelog/changes/001-create-users.yaml
  - include:
      file: db/changelog/changes/002-create-posts.yaml
```

```yaml
# db/changelog/changes/001-create-users.yaml
databaseChangeLog:
  - changeSet:
      id: 001-create-users
      author: developer
      changes:
        - createTable:
            tableName: users
            columns:
              - column:
                  name: id
                  type: BIGINT
                  autoIncrement: true
                  constraints:
                    primaryKey: true
              - column:
                  name: name
                  type: VARCHAR(100)
                  constraints:
                    nullable: false
              - column:
                  name: email
                  type: VARCHAR(255)
                  constraints:
                    nullable: false
                    unique: true
              - column:
                  name: created_at
                  type: TIMESTAMP
                  defaultValueComputed: NOW()
                  constraints:
                    nullable: false
        - createIndex:
            indexName: idx_user_email
            tableName: users
            unique: true
            columns:
              - column:
                  name: email
```

## Indexing Strategy

### When to Add Indexes

1. **Primary keys**: automatic, no action needed.
2. **Foreign keys**: always index foreign key columns. PostgreSQL does not auto-index them.
3. **Unique constraints**: always index columns used in uniqueness checks.
4. **WHERE clause columns**: index columns frequently used in filters.
5. **ORDER BY columns**: index columns used for sorting, especially with LIMIT.
6. **Composite indexes**: create when queries filter on multiple columns together. Put the most selective column first.

### Index Examples

```sql
-- Single column: for WHERE email = ?
CREATE UNIQUE INDEX idx_user_email ON users (email);

-- Composite: for WHERE active = true AND role = 'ADMIN'
CREATE INDEX idx_user_active_role ON users (active, role);

-- Partial index: only index active users (PostgreSQL)
CREATE INDEX idx_active_users ON users (email) WHERE active = true;

-- Covering index: includes columns to avoid table lookup
CREATE INDEX idx_post_list ON posts (status, created_at DESC) INCLUDE (title, author_id);

-- Text search (PostgreSQL)
CREATE INDEX idx_post_title_search ON posts USING gin (to_tsvector('english', title));
```

### When NOT to Add Indexes

- On very small tables (under a few hundred rows).
- On columns that are rarely queried.
- On columns with very low cardinality (e.g., a boolean with 50/50 distribution) unless part of a composite index.
- Too many indexes slow down INSERT/UPDATE operations.

## Repository Patterns

### Basic Repository

```java
public interface PostRepository extends JpaRepository<Post, Long> {

    List<Post> findByAuthorId(Long authorId);

    Page<Post> findByStatus(PostStatus status, Pageable pageable);

    Optional<Post> findByIdAndAuthorId(Long id, Long authorId);

    @Query("SELECT p FROM Post p WHERE p.author.id = :authorId AND p.status = :status")
    Page<Post> findByAuthorAndStatus(
            @Param("authorId") Long authorId,
            @Param("status") PostStatus status,
            Pageable pageable);

    @Modifying
    @Query("UPDATE Post p SET p.status = :status WHERE p.id = :id")
    int updateStatus(@Param("id") Long id, @Param("status") PostStatus status);

    @Query("SELECT p FROM Post p JOIN FETCH p.author WHERE p.id = :id")
    Optional<Post> findByIdWithAuthor(@Param("id") Long id);
}
```

### Avoiding N+1 Queries

Use `JOIN FETCH` or `@EntityGraph` when you know you need related entities:

```java
public interface PostRepository extends JpaRepository<Post, Long> {

    // Using JOIN FETCH
    @Query("SELECT p FROM Post p JOIN FETCH p.author JOIN FETCH p.comments WHERE p.id = :id")
    Optional<Post> findByIdFull(@Param("id") Long id);

    // Using EntityGraph
    @EntityGraph(attributePaths = {"author", "comments"})
    Optional<Post> findWithDetailsById(Long id);

    // For lists, use EntityGraph to batch-load
    @EntityGraph(attributePaths = {"author"})
    Page<Post> findByStatus(PostStatus status, Pageable pageable);
}
```

### Specification Pattern for Dynamic Queries

For complex search/filter scenarios:

```java
public class PostSpecifications {

    public static Specification<Post> hasStatus(PostStatus status) {
        return (root, query, cb) ->
                status == null ? null : cb.equal(root.get("status"), status);
    }

    public static Specification<Post> hasAuthor(Long authorId) {
        return (root, query, cb) ->
                authorId == null ? null : cb.equal(root.get("author").get("id"), authorId);
    }

    public static Specification<Post> titleContains(String search) {
        return (root, query, cb) ->
                search == null ? null : cb.like(cb.lower(root.get("title")),
                        "%" + search.toLowerCase() + "%");
    }

    public static Specification<Post> createdAfter(LocalDateTime date) {
        return (root, query, cb) ->
                date == null ? null : cb.greaterThanOrEqualTo(root.get("createdAt"), date);
    }
}
```

Make the repository extend `JpaSpecificationExecutor`:

```java
public interface PostRepository extends JpaRepository<Post, Long>,
        JpaSpecificationExecutor<Post> {
}
```

Use in the service:

```java
public Page<PostResponse> search(PostSearchRequest request, Pageable pageable) {
    Specification<Post> spec = Specification
            .where(PostSpecifications.hasStatus(request.getStatus()))
            .and(PostSpecifications.hasAuthor(request.getAuthorId()))
            .and(PostSpecifications.titleContains(request.getSearch()))
            .and(PostSpecifications.createdAfter(request.getFrom()));

    return postRepository.findAll(spec, pageable).map(postMapper::toResponse);
}
```

### Projections for Read-Only Queries

When you only need a subset of columns, use interface projections:

```java
public interface PostSummary {
    Long getId();
    String getTitle();
    PostStatus getStatus();
    LocalDateTime getCreatedAt();
    String getAuthorName();  // Derived from author.name via SpEL or naming convention
}

public interface PostRepository extends JpaRepository<Post, Long> {

    @Query("SELECT p.id AS id, p.title AS title, p.status AS status, " +
           "p.createdAt AS createdAt, p.author.name AS authorName " +
           "FROM Post p WHERE p.status = :status")
    Page<PostSummary> findSummariesByStatus(
            @Param("status") PostStatus status, Pageable pageable);
}
```

## Transaction Management

```java
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)  // Default: read-only for all methods
public class OrderService {

    private final OrderRepository orderRepository;
    private final InventoryService inventoryService;

    // Read-only: uses the class-level annotation
    public OrderResponse findById(Long id) {
        // ...
    }

    // Write: overrides with a read-write transaction
    @Transactional
    public OrderResponse createOrder(CreateOrderRequest request) {
        Order order = buildOrder(request);
        inventoryService.reserveItems(order.getItems()); // Same transaction
        return orderMapper.toResponse(orderRepository.save(order));
    }

    // Requires a NEW transaction regardless of the caller's context
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logOrderEvent(Long orderId, String event) {
        // Persists even if the caller's transaction rolls back
    }
}
```

## Rules to Follow

1. Always use `FetchType.LAZY` -- never rely on eager loading.
2. Never use `hibernate.ddl-auto=update` or `create` in production -- always use Flyway or Liquibase.
3. Always index foreign key columns.
4. Use `@Version` for optimistic locking on entities that can be concurrently updated.
5. Use `JOIN FETCH` or `@EntityGraph` to solve N+1 problems -- never load collections in a loop.
6. Use DTOs or projections for read queries -- do not return managed entities from the service layer.
7. Keep migrations small and incremental -- one concern per migration file.
8. Never modify an already-applied migration -- always create a new one.
9. Use `@Transactional(readOnly = true)` at the service class level and override with `@Transactional` on write methods.
10. Test your repository queries with `@DataJpaTest` and an embedded database (H2) or Testcontainers.
