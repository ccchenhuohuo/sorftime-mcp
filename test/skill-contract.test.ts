import { readFile, readdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { parse as parseYaml } from "yaml";

const root = resolve(process.cwd(), "skills/sorftime-research");
const text = (path: string): Promise<string> => readFile(join(root, path), "utf8");

describe("sorftime-research Skill contract", () => {
  it("uses minimal portable metadata and an implicit invocation policy", async () => {
    const skill = await text("SKILL.md");
    const match = /^---\n([\s\S]*?)\n---\n/u.exec(skill);
    expect(match).not.toBeNull();
    const metadata = parseYaml(match![1]!) as Record<string, unknown>;
    expect(Object.keys(metadata).sort()).toEqual(["description", "name"]);
    expect(metadata.name).toBe("sorftime-research");
    expect(String(metadata.description)).toContain("governed Sorftime MCP");
    expect(skill).not.toContain("TODO");

    const agent = parseYaml(await text("agents/openai.yaml")) as {
      interface?: { default_prompt?: string };
      policy?: { allow_implicit_invocation?: boolean };
    };
    expect(agent.interface?.default_prompt).toContain("$sorftime-research");
    expect(agent.policy?.allow_implicit_invocation).toBe(true);
  });

  it("documents all reader tools and keeps paid/mutating calls unavailable", async () => {
    const sources = [await text("SKILL.md"), await text("references/mcp-contract.md"), await text("references/workflows.md")].join("\n");
    for (const tool of ["sorftime_capabilities", "sorftime_check_quota", "sorftime_list_monitors", "sorftime_get_monitoring_results"]) {
      expect(sources).toContain(`\`${tool}\``);
    }
    expect(sources).toContain("paid reads");
    expect(sources).toContain("Never fall back to paid `ProductRequest`");
    expect(sources).toContain("Do not invoke its `api call`");
  });

  it("contains a lean portable reference and eval set", async () => {
    expect((await readdir(join(root, "references"))).sort()).toEqual([
      "interpretation-boundaries.md",
      "mcp-contract.md",
      "workflows.md",
    ]);
    const evals = JSON.parse(await text("evals/evals.json")) as {
      skill_name: string;
      evals: Array<{ id: number; prompt: string; expected_output: string }>;
    };
    expect(evals.skill_name).toBe("sorftime-research");
    expect(evals.evals).toHaveLength(12);
    expect(new Set(evals.evals.map((item) => item.id)).size).toBe(12);
    expect(new Set(evals.evals.map((item) => item.prompt)).size).toBe(12);
    const all = [
      await text("SKILL.md"), await text("agents/openai.yaml"),
      ...(await Promise.all((await readdir(join(root, "references"))).map((file) => text(`references/${file}`)))),
      JSON.stringify(evals),
    ].join("\n");
    expect(all).not.toMatch(/\/Users\//u);
  });
});
