package ch.janaka.mcp.spring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Spring Boot 4 + Spring AI 2.0: the same planner as an MCP server over Streamable HTTP at /mcp. */
@SpringBootApplication
public class PlannerApplication {
    public static void main(String[] args) {
        SpringApplication.run(PlannerApplication.class, args);
    }
}
