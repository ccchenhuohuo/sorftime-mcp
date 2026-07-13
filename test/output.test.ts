import { describe, expect, it } from "vitest";
import { prepareOutput, serializeOutput } from "../src/output.js";

describe("output serialization", () => {
  it("unwraps Data case-insensitively and selects a path", () => {
    const value = { Code: 0, Data: { rows: [{ ASIN: "B000TEST" }] } };
    expect(prepareOutput(value, { format: "json", dataOnly: true, select: "rows.0.ASIN" })).toBe("B000TEST");
  });

  it("emits valid CSV with nested fields escaped", () => {
    const output = serializeOutput([{ a: "hello,world", nested: { ok: true } }], { format: "csv" });
    expect(output).toBe('a,nested\n"hello,world","{""ok"":true}"');
  });

  it("emits one JSON value per line", () => {
    expect(serializeOutput([{ id: 1 }, { id: 2 }], { format: "jsonl" })).toBe('{"id":1}\n{"id":2}');
  });

  it("preserves exact strings for raw serialization", () => {
    expect(serializeOutput(` {"Code":0}\n`, { format: "raw" })).toBe(` {"Code":0}\n`);
  });
});
