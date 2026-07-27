@SpringBootApplication

@Configuration
- 表示这是一个 **配置类**
- 等价于 XML 里的 `<beans>`
- 允许你用 `@Bean` 定义对象

```java
@Configuration
public class AppConfig {
    @Bean
    public UserService userService() {
        return new UserService();
    }
}

```

@EnableAutoConfiguration
- **Spring Boot 最核心的能力**
- 根据：
    - classpath 里的依赖
    - application.yml
- **自动帮你装配 Bean**
    
例子：
- 有 `spring-boot-starter-web` → 自动配置 Tomcat + MVC
- 有 `spring-boot-starter-data-jpa` → 自动配置 JPA
- 有 `spring-cloud-starter-openfeign` → 自动配置 Feign

你 **不用写配置**，Spring Boot 帮你写好了。

@ComponentScan
- 自动扫描当前包及子包
- 找到：
    - `@Component`
    - `@Service`
    - `@Repository`
    - `@Controller`
- 并注册为 Bean

```java
@Service
public class OrderService {}

```