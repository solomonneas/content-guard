import { execFile } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_DIR = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = PLUGIN_DIR;

export default function register(api) {
  const cfg = api.pluginConfig ?? {};
  if (cfg.enabled === false) {
    api.logger.info("content-guard: disabled by config");
    return;
  }

  const allowedRecipients = new Set(cfg.allowedRecipients ?? []);
  const dryRun = cfg.dryRun === true;
  const rootDir = resolveMaybe(cfg.rootDir, PLUGIN_DIR) ?? DEFAULT_ROOT;
  const policyPath = resolveMaybe(cfg.policyPath, rootDir) ?? join(rootDir, "policies", "openclaw-message.json");
  const pythonCommand = cfg.pythonCommand ?? "python3";
  const timeoutMs = Number.isFinite(cfg.timeoutMs) ? cfg.timeoutMs : 5000;
  const failOpen = cfg.failOpen !== false;
  const failureReplacement = cfg.failureReplacement ?? "[content blocked by content-guard]";
  const includeOpf = cfg.opf === true;
  const opfDevice = cfg.opfDevice ?? "cpu";
  const opfBin = cfg.opfBin;

  api.logger.info(
    `content-guard: loaded policy=${policyPath} dryRun=${dryRun ? "true" : "false"} opf=${includeOpf ? "true" : "false"}`,
  );

  api.on("message_sending", async (event, ctx) => {
    const text = event.content;
    if (!text) return;

    if (event.to && allowedRecipients.has(event.to)) {
      return;
    }

    const result = await redactWithContentGuard({
      text,
      rootDir,
      policyPath,
      pythonCommand,
      timeoutMs,
      includeOpf,
      opfDevice,
      opfBin,
    });

    if (!result.ok) {
      const target = ctx.channelId ?? event.to ?? "unknown";
      api.logger.error(`content-guard: failed for ${target}: ${result.error}`);
      if (failOpen) {
        return;
      }
      return { content: failureReplacement };
    }

    if (result.redacted === text) {
      return;
    }

    const target = ctx.channelId ?? event.to ?? "unknown";
    if (dryRun) {
      api.logger.warn(`content-guard: [DRY-RUN] would redact outbound message to ${target}`);
      return;
    }

    api.logger.info(`content-guard: redacted outbound message to ${target}`);
    return { content: result.redacted };
  });
}
function resolveMaybe(value, baseDir) {
  if (!value) return undefined;
  return isAbsolute(value) ? value : resolve(baseDir, value);
}

async function redactWithContentGuard(options) {
  const dir = await mkdtemp(join(tmpdir(), "content-guard-"));
  const inputPath = join(dir, "message.txt");
  try {
    await writeFile(inputPath, options.text, "utf8");
    const args = [
      "-m",
      "content_guard",
      "redact",
      inputPath,
      "--policy",
      options.policyPath,
    ];

    if (options.includeOpf) {
      args.push("--opf", "--opf-device", options.opfDevice);
    }

    const env = {
      ...process.env,
      PYTHONPATH: buildPythonPath(join(options.rootDir, "src"), process.env.PYTHONPATH),
    };
    if (options.opfBin) {
      env.CONTENT_GUARD_OPF_BIN = options.opfBin;
    }

    const proc = await execFileCapture(options.pythonCommand, args, {
      env,
      timeout: options.timeoutMs,
      maxBuffer: 1024 * 1024,
    });

    if (proc.stdout) {
      return { ok: true, redacted: proc.stdout };
    }

    if (proc.code === 0) {
      const fallback = await readFile(inputPath, "utf8");
      return { ok: true, redacted: fallback };
    }

    return {
      ok: false,
      redacted: options.text,
      error: (proc.stderr || proc.error || `content_guard exited ${proc.code}`).trim(),
    };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

function buildPythonPath(requiredPath, existingPath) {
  if (!existingPath) return requiredPath;
  return `${requiredPath}:${existingPath}`;
}

function execFileCapture(command, args, options) {
  return new Promise((resolveResult) => {
    execFile(command, args, options, (error, stdout, stderr) => {
      resolveResult({
        code: typeof error?.code === "number" ? error.code : 0,
        error: error ? String(error.message ?? error) : "",
        stdout: String(stdout ?? ""),
        stderr: String(stderr ?? ""),
      });
    });
  });
}
