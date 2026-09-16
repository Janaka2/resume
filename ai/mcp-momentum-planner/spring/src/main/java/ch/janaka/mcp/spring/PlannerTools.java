package ch.janaka.mcp.spring;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import ch.janaka.mcp.PlanContract;
import ch.janaka.mcp.PlanValidator;

/**
 * The planner's tools as Spring beans. Spring AI reads the method signatures, builds the JSON schemas,
 * registers the tools with the MCP server and serves them at /mcp. No protocol code anywhere.
 */
@Component
public class PlannerTools {

    private final Path store;

    public PlannerTools(@Value("${planner.store:plans}") String store) {
        this.store = Path.of(store);
    }

    @McpTool(name = "get_plan_contract",
             description = "The rules, categories, limits and JSON shape a plan must follow. Call this before drafting a plan.",
             annotations = @McpTool.McpAnnotations(readOnlyHint = true, idempotentHint = true, openWorldHint = false))
    public Map<String, Object> getPlanContract() {
        return PlanContract.asMap();
    }

    @McpTool(name = "validate_plan",
             description = "Judge a drafted plan against the request it answers. Deterministic, calls no model, stores nothing. "
                 + "Returns valid, errors (each with a JSON path and what to fix), warnings and the checks performed.",
             annotations = @McpTool.McpAnnotations(readOnlyHint = true, idempotentHint = true, openWorldHint = false))
    public PlanValidator.Verdict validatePlan(
            @McpToolParam(description = "The drafted plan as a JSON object", required = true) Map<String, Object> plan,
            @McpToolParam(description = "The plan request, exactly as the person gave it", required = true) Map<String, Object> request) {
        return PlanValidator.validate(plan, request);
    }

    @McpTool(name = "save_plan",
             description = "Save a plan that validates. An invalid plan is refused with the errors, so the caller can fix and retry.",
             annotations = @McpTool.McpAnnotations(readOnlyHint = false, destructiveHint = false, idempotentHint = true, openWorldHint = false))
    public Map<String, Object> savePlan(
            @McpToolParam(description = "The drafted plan as a JSON object", required = true) Map<String, Object> plan,
            @McpToolParam(description = "The plan request, exactly as the person gave it", required = true) Map<String, Object> request)
            throws IOException {
        PlanValidator.Verdict verdict = PlanValidator.validate(plan, request);
        if (!verdict.valid()) {
            StringBuilder sb = new StringBuilder("Plan not saved.");
            verdict.errors().forEach(e -> sb.append(" | ").append(e.path()).append(": ").append(e.message()));
            throw new IllegalArgumentException(sb.toString());   // becomes a tool result with isError: true
        }
        String planId = String.valueOf(plan.get("requestId"));
        Files.createDirectories(store);
        Files.writeString(store.resolve(planId + ".json"), Json.write(plan), StandardCharsets.UTF_8);
        return Map.of("saved", true, "planId", planId, "uri", "plan://" + planId, "warnings", verdict.warnings());
    }

    /** Tiny JSON writer so this class does not depend on a particular Jackson version. */
    static final class Json {
        static String write(Object v) {
            if (v == null) return "null";
            if (v instanceof String s) return '"' + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + '"';
            if (v instanceof Number || v instanceof Boolean) return v.toString();
            if (v instanceof Map<?, ?> m) {
                StringBuilder sb = new StringBuilder("{");
                m.forEach((k, val) -> sb.append(sb.length() > 1 ? "," : "").append(write(String.valueOf(k))).append(':').append(write(val)));
                return sb.append('}').toString();
            }
            if (v instanceof List<?> l) {
                StringBuilder sb = new StringBuilder("[");
                l.forEach(val -> sb.append(sb.length() > 1 ? "," : "").append(write(val)));
                return sb.append(']').toString();
            }
            return write(v.toString());
        }
    }
}
