package ch.janaka.mcp;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Pattern;

/**
 * Judges a drafted plan against the request it answers.
 * Deterministic, calls no model, stores nothing. Every error carries a JSON path and a fix,
 * which is what lets a model correct its own draft.
 */
public final class PlanValidator {

    public record Issue(String code, String path, String message) {}

    public record Verdict(boolean valid, List<Issue> errors, List<Issue> warnings, List<String> checks) {}

    private static final Pattern HHMM = Pattern.compile("^([01][0-9]|2[0-3]):[0-5][0-9]$");

    private final List<Issue> errors = new ArrayList<>();
    private final List<Issue> warnings = new ArrayList<>();
    private final List<String> checks = new ArrayList<>();
    private final Map<String, Object> request;

    private PlanValidator(Map<String, Object> request) { this.request = request; }

    public static Verdict validate(Map<String, Object> plan, Map<String, Object> request) {
        return new PlanValidator(request).run(plan);
    }

    private void err(String code, String path, String message) { errors.add(new Issue(code, path, message)); }

    @SuppressWarnings("unchecked")
    private Verdict run(Map<String, Object> plan) {
        checks.add("envelope");
        if (!PlanContract.FORMAT.equals(plan.get("format")))
            err("format", "$.format", "must be \"" + PlanContract.FORMAT + "\"");
        if (!Integer.valueOf(PlanContract.CONTRACT_VERSION).equals(plan.get("contractVersion")))
            err("contractVersion", "$.contractVersion", "must be " + PlanContract.CONTRACT_VERSION);
        Object kind = plan.get("kind");
        if (!"routine".equals(kind) && !"goal".equals(kind))
            err("kind", "$.kind", "must be \"routine\" or \"goal\"");
        for (String field : List.of("name", "tagline", "description")) {
            Object v = plan.get(field);
            if (!(v instanceof String s) || s.isBlank()) err("required", "$." + field, field + " is required");
            else if (s.length() > PlanContract.LIMITS.get(field))
                err("length", "$." + field, field + " is longer than " + PlanContract.LIMITS.get(field) + " characters");
        }

        checks.add("request");
        if (!Objects.equals(plan.get("requestId"), request.get("requestId")))
            err("requestId", "$.requestId", "must echo the request id \"" + request.get("requestId") + "\"");
        if (!Objects.equals(plan.get("request"), request))
            err("request", "$.request", "must echo the request object exactly as given");
        if (kind != null && !kind.equals(request.get("kind")))
            err("kind", "$.kind", "the request asked for a \"" + request.get("kind") + "\" plan");

        checks.add("fields");
        checks.add("day-shape");
        checks.add("commitments");
        if ("routine".equals(kind)) {
            Map<String, Object> routine = (Map<String, Object>) plan.getOrDefault("routine", Map.of());
            checkBlocks((List<Map<String, Object>>) routine.get("blocks"), "$.routine.blocks", null);
            Map<String, Object> weekdays = (Map<String, Object>) routine.getOrDefault("weekdays", Map.of());
            for (var day : weekdays.entrySet()) {
                if (!PlanContract.WEEKDAYS.contains(day.getKey())) {
                    err("weekday", "$.routine.weekdays." + day.getKey(), "use mon..sun");
                    continue;
                }
                checkBlocks((List<Map<String, Object>>) day.getValue(), "$.routine.weekdays." + day.getKey(), day.getKey());
            }
        }

        checks.add("feasibility");
        if ("goal".equals(kind)) {
            Map<String, Object> goal = (Map<String, Object>) plan.getOrDefault("goal", Map.of());
            Object days = goal.get("days");
            if (!(days instanceof List<?> dayList) || dayList.isEmpty()) {
                err("required", "$.goal.days", "needs at least one day");
            } else {
                if (request.get("days") instanceof Integer wanted && wanted != dayList.size())
                    err("days", "$.goal.days", "the request asked for " + wanted + " days, the plan has " + dayList.size());
                for (int d = 0; d < dayList.size(); d++) {
                    Map<String, Object> day = (Map<String, Object>) dayList.get(d);
                    List<Map<String, Object>> acts = (List<Map<String, Object>>) day.getOrDefault("activities", List.of());
                    int total = 0;
                    for (int a = 0; a < acts.size(); a++) {
                        String p = "$.goal.days[" + d + "].activities[" + a + "]";
                        Map<String, Object> act = acts.get(a);
                        if (!PlanContract.CATEGORIES.containsKey(String.valueOf(act.get("category"))))
                            err("category", p + ".category", "use one of " + String.join(", ", PlanContract.CATEGORIES.keySet()));
                        if (act.get("minutes") instanceof Integer mins && mins >= 1 && mins <= PlanContract.LIMITS.get("minutesPerActivity"))
                            total += mins;
                        else
                            err("duration", p + ".minutes", "must be 1.." + PlanContract.LIMITS.get("minutesPerActivity"));
                        for (String field : List.of("title", "activity", "guidance", "doneWhen"))
                            if (!(act.get(field) instanceof String s) || s.isBlank()) err("required", p + "." + field, field + " is required");
                    }
                    if (total > PlanContract.LIMITS.get("minutesPerDay"))
                        err("feasibility", "$.goal.days[" + d + "]", total + " minutes do not fit in one day");
                }
            }
        }
        return new Verdict(errors.isEmpty(), List.copyOf(errors), List.copyOf(warnings), List.copyOf(checks));
    }

    private static int minutes(String hhmm) {
        return Integer.parseInt(hhmm.substring(0, 2)) * 60 + Integer.parseInt(hhmm.substring(3));
    }

    @SuppressWarnings("unchecked")
    private void checkBlocks(List<Map<String, Object>> blocks, String path, String weekday) {
        if (blocks == null || blocks.isEmpty()) { err("required", path, "needs at least one block"); return; }
        if (blocks.size() > PlanContract.LIMITS.get("blocksPerDay"))
            err("limit", path, "more than " + PlanContract.LIMITS.get("blocksPerDay") + " blocks in one day");
        List<Map<String, Object>> commitments = (List<Map<String, Object>>) request.getOrDefault("commitments", List.of());
        int prevEnd = -1;
        for (int i = 0; i < blocks.size(); i++) {
            Map<String, Object> b = blocks.get(i);
            String p = path + "[" + i + "]";
            if (!(b.get("start") instanceof String start) || !HHMM.matcher(start).matches()) {
                err("time", p + ".start", "must be HH:MM, 24-hour"); continue;
            }
            if (!(b.get("durationMin") instanceof Integer dur) || dur < 1 || dur > PlanContract.LIMITS.get("minutesPerActivity")) {
                err("duration", p + ".durationMin", "must be 1.." + PlanContract.LIMITS.get("minutesPerActivity") + " minutes"); continue;
            }
            if (!PlanContract.CATEGORIES.containsKey(String.valueOf(b.get("category"))))
                err("category", p + ".category", "use one of " + String.join(", ", PlanContract.CATEGORIES.keySet()));
            if (!(b.get("activity") instanceof String activity) || activity.length() > PlanContract.LIMITS.get("activity"))
                err("activity", p + ".activity", "a short name up to " + PlanContract.LIMITS.get("activity") + " characters");
            if (!(b.get("essential") instanceof Boolean))
                err("essential", p + ".essential", "must be true or false");

            int s = minutes(start), e = s + dur;
            if (s < prevEnd)
                err("overlap", p, "\"" + b.get("activity") + "\" starts before the previous block ends ("
                    + "%02d:%02d".formatted(prevEnd / 60, prevEnd % 60) + ")");
            if (e > 1440) {
                boolean lastRest = i == blocks.size() - 1 && "rest".equals(b.get("category"));
                if (lastRest) warnings.add(new Issue("overnight", p, "\"" + b.get("activity") + "\" runs past midnight, as sleep does"));
                else err("midnight", p, "must end by 24:00");
            }
            prevEnd = e;

            for (Map<String, Object> c : commitments) {
                List<String> days = (List<String>) c.getOrDefault("days", List.of());
                if (weekday != null && !days.contains(weekday)) continue;
                int cs = minutes((String) c.get("start")), ce = minutes((String) c.get("end"));
                if (s < ce && e > cs && !Objects.equals(b.get("activity"), c.get("label")))
                    err("commitment", p, "\"" + b.get("activity") + "\" overlaps the commitment \"" + c.get("label")
                        + "\" (" + c.get("start") + "–" + c.get("end") + ")");
            }
        }
    }
}
