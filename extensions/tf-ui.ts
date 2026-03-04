/**
 * Extension command for launching the pi-tk-flow TUI.
 *
 * Provides /tf ui for terminal mode and /tf ui --web for web mode.
 */

import { execSync, spawn } from "child_process";
import { existsSync } from "fs";
import { resolve } from "path";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

/**
 * Check if Python is available
 */
function checkPython(): { available: boolean; command: string; version?: string } {
  const candidates = ["python3", "python"];

  for (const cmd of candidates) {
    try {
      const version = execSync(`${cmd} --version`, { encoding: "utf-8", stdio: ["pipe", "pipe", "ignore"] });
      return { available: true, command: cmd, version: version.trim() };
    } catch {
      continue;
    }
  }

  return { available: false, command: "" };
}

/**
 * Check if the pi_tk_flow_ui package is importable
 */
function checkUIPackage(pythonCmd: string): { installed: boolean; error?: string } {
  try {
    execSync(
      `${pythonCmd} -c "import pi_tk_flow_ui"`,
      { encoding: "utf-8", stdio: ["pipe", "pipe", "ignore"] }
    );
    return { installed: true };
  } catch (error) {
    return {
      installed: false,
      error: "pi_tk_flow_ui package not found"
    };
  }
}

/**
 * Check if Textual is installed
 */
function checkTextual(pythonCmd: string): { installed: boolean } {
  try {
    execSync(
      `${pythonCmd} -c "import textual"`,
      { encoding: "utf-8", stdio: ["pipe", "pipe", "ignore"] }
    );
    return { installed: true };
  } catch {
    return { installed: false };
  }
}

/**
 * Find the Python package directory
 */
function findPythonPackage(cwd: string): string | null {
  const candidates = [
    resolve(cwd, "python"),
    resolve(cwd, "..", "python"),
    resolve(cwd, "pi-tk-flow", "python"),
  ];

  for (const path of candidates) {
    if (existsSync(resolve(path, "pyproject.toml"))) {
      return path;
    }
  }

  return null;
}

/**
 * Launch the TUI in terminal mode
 */
function launchTerminal(pythonCmd: string, cwd: string, reply: (msg: string) => void): void {
  // Check package availability
  const packageCheck = checkUIPackage(pythonCmd);
  if (!packageCheck.installed) {
    const pythonPackage = findPythonPackage(cwd);

    reply("Error: pi_tk_flow_ui dependencies not installed.\n");

    if (pythonPackage) {
      reply("Install with one of:\n");
      reply(`  cd "${pythonPackage}" && pip install -e '.[ui]'\n`);
      reply(`  cd "${pythonPackage}" && uv pip install -e '.[ui]'\n`);
    } else {
      reply("Install with:\n");
      reply("  pip install -e ./python[ui]\n");
      reply("  # or\n");
      reply("  uv pip install -e ./python[ui]\n");
    }

    return;
  }

  // Check Textual
  const textualCheck = checkTextual(pythonCmd);
  if (!textualCheck.installed) {
    reply("Error: Textual is not installed.\n");
    reply("Install with: pip install textual>=0.47.0\n");
    return;
  }

  // Launch the TUI
  reply("Launching Ticketflow UI...\n");

  const proc = spawn(pythonCmd, ["-m", "pi_tk_flow_ui"], {
    cwd,
    stdio: "inherit",
    detached: false,
  });

  proc.on("error", (err) => {
    reply(`Failed to launch TUI: ${err.message}\n`);
  });

  // Wait for process to complete
  proc.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      reply(`\nTUI exited with code ${code}\n`);
    } else {
      reply("\nTUI closed.\n");
    }
  });
}

/**
 * Print web mode command
 */
function printWebCommand(pythonCmd: string, args: string[], reply: (msg: string) => void): void {
  // Parse optional host/port
  let host = "127.0.0.1";
  let port = "8000";

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--host" && args[i + 1]) {
      host = args[i + 1];
      i++;
    } else if (args[i] === "--port" && args[i + 1]) {
      port = args[i + 1];
      i++;
    } else if (args[i].startsWith("--host=")) {
      host = args[i].split("=")[1];
    } else if (args[i].startsWith("--port=")) {
      port = args[i].split("=")[1];
    }
  }

  reply("\n🌐 To serve the Ticketflow UI in a web browser, run:\n");
  reply("\n");
  reply(`   textual serve "${pythonCmd} -m pi_tk_flow_ui" --host ${host} --port ${port}\n`);
  reply("\n");
  reply("⚠️  WARNING: Security considerations for web serving:\n");
  reply("   • The default host (127.0.0.1) only allows local access\n");
  reply("   • Use --host 0.0.0.0 to bind to all interfaces (allows external access)\n");
  reply("   • Binding to 0.0.0.0 exposes the UI on your network - ensure proper firewall rules\n");
  reply("   • No authentication is provided - anyone with access can view tickets\n");
  reply("\n");
}

/**
 * TF UI Extension - Registers /tf ui command with pi
 */
export default function tfUiExtension(pi: ExtensionAPI) {
  pi.registerCommand("tf ui", {
    description: "Launch the Ticketflow UI (terminal or web)",
    examples: [
      "/tf ui",
      "/tf ui --web",
      "/tf ui --web --host 0.0.0.0 --port 8080",
    ],
    handler: async (args: string[], ctx: { cwd: string; reply: (msg: string) => void }) => {
      const { cwd, reply } = ctx;

      // Check Python first
      const pythonCheck = checkPython();
      if (!pythonCheck.available) {
        reply("Error: Python 3.10+ is required for the TUI.\n");
        reply("Install Python: https://www.python.org/downloads/\n");
        reply("\nAlternatively, ensure 'python' or 'python3' is in your PATH.\n");
        return;
      }

      // Show Python version in debug mode
      if (args.includes("--debug")) {
        reply(`Using ${pythonCheck.version}\n`);
      }

      // Check for --web flag
      const isWebMode = args.includes("--web");

      if (isWebMode) {
        printWebCommand(pythonCheck.command, args, reply);
      } else {
        launchTerminal(pythonCheck.command, cwd, reply);
      }
    },
  });
}
