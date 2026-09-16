package ch.janaka.mcp;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import io.modelcontextprotocol.json.McpJsonMapper;
import io.modelcontextprotocol.json.TypeRef;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.McpSyncServerExchange;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpError;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpSchema.CallToolRequest;
import io.modelcontextprotocol.spec.McpSchema.CallToolResult;
import io.modelcontextprotocol.spec.McpSchema.ElicitResult;
import io.modelcontextprotocol.spec.McpSchema.ServerCapabilities;
import io.modelcontextprotocol.spec.McpSchema.TextContent;
import io.modelcontextprotocol.spec.McpSchema.Tool;
import io.modelcontextprotocol.spec.McpSchema.ToolAnnotations;
import io.modelcontextprotocol.json.McpJsonDefaults;

/**
 * An MCP server for AI-drafted daily plans, on the official MCP Java SDK 2.0.
 *
 * Tools:     get_plan_contract, validate_plan, save_plan
 * Resource:  plan://{planId}
 * Prompt:    draft-plan
 * Transport: stdio (stdout is the protocol channel; all logging goes to stderr via slf4j-simple)
 *
 * Build: mvn -q package     Run: java -jar target/momentum-planner.jar
 */
public final class MomentumPlannerServer {

    private static final McpJsonMapper JSON = McpJsonDefaults.getMapper();
    private static final TypeRef<Map<String, Object>> MAP = new TypeRef<>() {};
    private static final Path STORE = Path.of(System.getProperty("plan.store", "plans"));

    public static void main(String[] args) {
        McpSyncServer server = McpServer.sync(new StdioServerTransportProvider(JSON))
            .serverInfo("momentum-planner", "1.0.0")
            .instructions("Tools for AI-drafted daily plans. Call get_plan_contract before drafting, "
                + "validate_plan after drafting, and save_plan only once validate_plan says valid.")
            .capabilities(ServerCapabilities.builder().tools(true).resources(false, true).prompts(true).build())
            .tools(contractTool(), validateTool(), saveTool())
            .resourceTemplates(planResource())
            .prompts(draftPrompt())
            .build();
        Runtime.getRuntime().addShutdownHook(new Thread(server::close));
        // stdio: the transport now owns the process. Main returns; the server lives until stdin closes.
    }

    // ------------------------------------------------------------ tools

    /** JSON Schema for a tool that takes a plan and its request. Shared by validate_plan and save_plan. */
    private static Map<String, Object> planAndRequestSchema() {
        return Map.of(
            "type", "object",
            "properties", Map.of(
                "plan", Map.of("description", "The drafted plan: the JSON object, or its text",
                               "anyOf", List.of(Map.of("type", "object"), Map.of("type", "string"))),
                "request", Map.of("type", "object", "description", "The plan request, exactly as the person gave it")),
            "required", List.of("plan", "request"));
    }

    private static McpServerFeatures.SyncToolSpecification contractTool() {
        Tool tool = Tool.builder("get_plan_contract", Map.of("type", "object", "additionalProperties", false))
            .title("Plan contract")
            .description("The rules, categories, limits and JSON shape a plan must follow. Call this before drafting a plan.")
            .annotations(new ToolAnnotations(null, true, false, true, false, null))
            .build();
        return McpServerFeatures.SyncToolSpecification.builder()
            .tool(tool)
            .callHandler((exchange, request) -> structured(PlanContract.asMap(), false))
            .build();
    }

    private static McpServerFeatures.SyncToolSpecification validateTool() {
        Tool tool = Tool.builder("validate_plan", planAndRequestSchema())
            .title("Validate a plan")
            .description("Judge a drafted plan against the request it answers. Deterministic, calls no model, stores nothing. "
                + "Returns valid, errors (each with a JSON path and what to fix), warnings and the checks performed.")
            .annotations(new ToolAnnotations(null, true, false, true, false, null))
            .build();
        return McpServerFeatures.SyncToolSpecification.builder()
            .tool(tool)
            .callHandler((exchange, request) -> {
                Map<String, Object> plan = planArgument(request);
                if (plan == null) return error("plan is not valid JSON");
                PlanValidator.Verdict verdict = PlanValidator.validate(plan, requestArgument(request));
                return structured(JSON.convertValue(verdict, MAP), false);
            })
            .build();
    }

    private static McpServerFeatures.SyncToolSpecification saveTool() {
        Tool tool = Tool.builder("save_plan", planAndRequestSchema())
            .title("Save a plan")
            .description("Save a plan that validates. An invalid plan is refused with the errors, so the caller can fix and retry.")
            .annotations(new ToolAnnotations(null, false, false, true, false, null))
            .build();
        return McpServerFeatures.SyncToolSpecification.builder()
            .tool(tool)
            .callHandler(MomentumPlannerServer::save)
            .build();
    }

    private static CallToolResult save(McpSyncServerExchange exchange, CallToolRequest request) {
        Map<String, Object> plan = planArgument(request);
        if (plan == null) return error("plan is not valid JSON");
        PlanValidator.Verdict verdict = PlanValidator.validate(plan, requestArgument(request));
        if (!verdict.valid()) {
            StringBuilder sb = new StringBuilder("Plan not saved.");
            verdict.errors().forEach(e -> sb.append(" | ").append(e.path()).append(": ").append(e.message()));
            return error(sb.toString());                       // isError: true, so the model can fix and retry
        }
        String planId = String.valueOf(plan.get("requestId"));
        Path file = STORE.resolve(planId + ".json");
        try {
            if (Files.exists(file) && !confirmOverwrite(exchange)) {
                return structured(Map.of("saved", false, "planId", planId, "uri", "plan://" + planId), false);
            }
            Files.createDirectories(STORE);
            Files.writeString(file, JSON.writeValueAsString(plan), StandardCharsets.UTF_8);
        } catch (IOException e) {
            return error("could not write the plan: " + e.getMessage());
        }
        return structured(Map.of("saved", true, "planId", planId, "uri", "plan://" + planId,
            "warnings", JSON.convertValue(verdict.warnings(), new TypeRef<List<Map<String, Object>>>() {})), false);
    }

    /** Elicitation: ask the person before replacing a saved plan. Only when the client supports it. */
    private static boolean confirmOverwrite(McpSyncServerExchange exchange) {
        if (exchange.getClientCapabilities() == null || exchange.getClientCapabilities().elicitation() == null) {
            return false;                                       // no way to ask: refuse rather than guess
        }
        var ask = McpSchema.ElicitRequest.builder(
                "A plan with this requestId is already saved. Overwrite it?",
                Map.of("type", "object",
                       "properties", Map.of("overwrite", Map.of("type", "boolean", "description", "Replace the saved plan")),
                       "required", List.of("overwrite")))
            .build();
        ElicitResult answer = exchange.createElicitation(ask);
        return answer.action() == ElicitResult.Action.ACCEPT
            && answer.content() != null
            && Boolean.TRUE.equals(answer.content().get("overwrite"));
    }

    // ------------------------------------------------------------ resource and prompt

    private static McpServerFeatures.SyncResourceTemplateSpecification planResource() {
        var template = McpSchema.ResourceTemplate.builder("plan://{planId}", "Saved plan")
            .description("A saved plan, as JSON")
            .mimeType("application/json")
            .build();
        return new McpServerFeatures.SyncResourceTemplateSpecification(template, (exchange, request) -> {
            String planId = request.uri().substring("plan://".length());
            Path file = STORE.resolve(planId + ".json");
            String text;
            try {
                text = Files.readString(file, StandardCharsets.UTF_8);
            } catch (IOException e) {
                throw McpError.builder(McpSchema.ErrorCodes.INVALID_PARAMS).message("no plan saved as " + planId).build();
            }
            return McpSchema.ReadResourceResult.builder(List.of(
                    McpSchema.TextResourceContents.builder(request.uri(), text).mimeType("application/json").build()))
                .build();
        });
    }

    private static McpServerFeatures.SyncPromptSpecification draftPrompt() {
        var prompt = McpSchema.Prompt.builder("draft-plan")
            .description("Instructions for drafting a plan from a request. Use with get_plan_contract.")
            .arguments(List.of(McpSchema.PromptArgument.builder("request_json")
                .description("The plan request as JSON").required(true).build()))
            .build();
        return new McpServerFeatures.SyncPromptSpecification(prompt, (exchange, request) -> {
            String text = "Call get_plan_contract, then draft one plan for this request as a single JSON document that "
                + "follows the contract. Then call validate_plan with the plan and the request, fix every error it reports, "
                + "and only when it returns valid: true call save_plan.\n\nRequest:\n" + request.arguments().get("request_json");
            return McpSchema.GetPromptResult.builder(List.of(
                    McpSchema.PromptMessage.builder(McpSchema.Role.USER, TextContent.builder(text).build()).build()))
                .build();
        });
    }

    // ------------------------------------------------------------ helpers

    /** The plan argument may arrive as a JSON object or as the model's JSON text. */
    @SuppressWarnings("unchecked")
    private static Map<String, Object> planArgument(CallToolRequest request) {
        Object plan = request.arguments().get("plan");
        if (plan instanceof Map<?, ?> m) return (Map<String, Object>) m;
        if (plan instanceof String s) {
            try { return JSON.readValue(s, MAP); } catch (IOException e) { return null; }
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> requestArgument(CallToolRequest request) {
        Object r = request.arguments().get("request");
        return r instanceof Map<?, ?> m ? (Map<String, Object>) m : Map.of();
    }

    /** Structured content for programs, plus the same JSON as text for the model. */
    private static CallToolResult structured(Object value, boolean isError) {
        String text;
        try { text = JSON.writeValueAsString(value); } catch (IOException e) { text = String.valueOf(value); }
        return CallToolResult.builder().addTextContent(text).structuredContent(value).isError(isError).build();
    }

    private static CallToolResult error(String message) {
        return CallToolResult.builder().addTextContent(message).isError(true).build();
    }

    private MomentumPlannerServer() {}
}
