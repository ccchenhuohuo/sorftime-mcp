#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");

const userArgs = process.argv.slice(2);
const pythonArgs = userArgs.length === 0 ? ["stdio"] : userArgs;
const pythonPackage = "sorftime-mcp==0.1.1";
const child = spawn(
  "uvx",
  ["--from", pythonPackage, "sorftime-mcp", ...pythonArgs],
  {
    env: process.env,
    stdio: "inherit"
  }
);

child.on("error", (error) => {
  if (error.code === "ENOENT") {
    console.error("未找到 uvx。请先安装 uv：https://docs.astral.sh/uv/getting-started/installation/");
    process.exit(127);
  }
  console.error(`启动 sorftime-mcp 失败：${error.message}`);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});
