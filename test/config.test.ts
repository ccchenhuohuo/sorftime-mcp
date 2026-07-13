import { mkdtemp, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { configPath, deleteToken, loadConfig, resolveToken, saveConfig, saveToken } from "../src/config.js";

describe("configuration and credentials", () => {
  const originalStore = process.env.SORFTIME_CREDENTIAL_STORE;
  afterEach(() => {
    if (originalStore === undefined) delete process.env.SORFTIME_CREDENTIAL_STORE;
    else process.env.SORFTIME_CREDENTIAL_STORE = originalStore;
  });

  it("writes non-secret config atomically with mode 0600", async () => {
    const directory = await mkdtemp(join(tmpdir(), "sorftime-config-"));
    const env = { ...process.env, SORFTIME_CONFIG_DIR: directory };
    await saveConfig({ domain: "jp", timeoutMs: 120_000 }, env);
    expect(await loadConfig(env)).toEqual({ domain: "jp", timeoutMs: 120_000 });
    expect((await stat(configPath(env))).mode & 0o777).toBe(0o600);
  });

  it("uses environment credentials before stored credentials", async () => {
    const directory = await mkdtemp(join(tmpdir(), "sorftime-creds-"));
    const env = {
      ...process.env,
      SORFTIME_CONFIG_DIR: directory,
      SORFTIME_CREDENTIAL_STORE: "file",
      SORFTIME_ACCOUNT_SK: "environment-sentinel",
    };
    await saveToken("file-sentinel", env);
    expect(await resolveToken(undefined, env)).toEqual({ token: "environment-sentinel", source: "environment" });
    const stored = await readFile(join(directory, "credentials.json"), "utf8");
    expect(stored).toContain("file-sentinel");
    expect((await stat(join(directory, "credentials.json"))).mode & 0o777).toBe(0o600);
    expect(await deleteToken(env)).toBe(true);
  });

  it("refuses legacy secret-like config keys and strips unknown benign keys", async () => {
    const directory = await mkdtemp(join(tmpdir(), "sorftime-sanitize-"));
    const env = { ...process.env, SORFTIME_CONFIG_DIR: directory };
    await writeFile(configPath(env), JSON.stringify({ domain: "us", futureSetting: true }));
    expect(await loadConfig(env)).toEqual({ domain: "us" });
    await writeFile(configPath(env), JSON.stringify({ domain: "us", accountSk: "must-not-print" }));
    await expect(loadConfig(env)).rejects.toThrow(/Secret-like key/u);
  });
});
