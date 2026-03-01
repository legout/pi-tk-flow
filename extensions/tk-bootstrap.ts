import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

type Scope = "user" | "project";

type InstallStats = {
	created: string[];
	updated: string[];
	unchanged: string[];
};

function parseScope(args: string): Scope {
	const normalized = args.trim().toLowerCase();
	if (!normalized) return "user";

	const projectMatch = normalized.match(/(?:^|\s)--scope(?:\s+|=)project(?:\s|$)/);
	if (projectMatch || normalized === "project") return "project";

	const userMatch = normalized.match(/(?:^|\s)--scope(?:\s+|=)user(?:\s|$)/);
	if (userMatch || normalized === "user") return "user";

	return "user";
}

function parseFlag(args: string, flag: string): boolean {
	const escaped = flag.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	return new RegExp(`(?:^|\\s)${escaped}(?:\\s|$)`).test(args);
}

async function ensureDir(dir: string): Promise<void> {
	await fs.mkdir(dir, { recursive: true });
}

async function readIfExists(file: string): Promise<string | null> {
	try {
		return await fs.readFile(file, "utf8");
	} catch {
		return null;
	}
}

async function listTemplates(srcDir: string, suffix: string): Promise<string[]> {
	const entries = await fs.readdir(srcDir, { withFileTypes: true });
	return entries.filter((e) => e.isFile() && e.name.endsWith(suffix)).map((e) => e.name).sort();
}

async function installTemplates(
	srcDir: string,
	dstDir: string,
	fileNames: string[],
	dryRun: boolean,
): Promise<InstallStats> {
	const created: string[] = [];
	const updated: string[] = [];
	const unchanged: string[] = [];

	for (const fileName of fileNames) {
		const src = path.join(srcDir, fileName);
		const dst = path.join(dstDir, fileName);
		const srcContent = await fs.readFile(src, "utf8");
		const dstContent = await readIfExists(dst);

		if (dstContent === null) {
			created.push(fileName);
			if (!dryRun) await fs.writeFile(dst, srcContent, "utf8");
			continue;
		}

		if (dstContent !== srcContent) {
			updated.push(fileName);
			if (!dryRun) await fs.writeFile(dst, srcContent, "utf8");
		} else {
			unchanged.push(fileName);
		}
	}

	return { created, updated, unchanged };
}

export default function tkBootstrapExtension(pi: ExtensionAPI) {
	const __filename = fileURLToPath(import.meta.url);
	const __dirname = path.dirname(__filename);
	const agentsTemplateDir = path.resolve(__dirname, "..", "assets", "agents");
	const chainsTemplateDir = path.resolve(__dirname, "..", "assets", "chains");

	pi.registerCommand("tk-bootstrap", {
		description:
			"Install/update tk workflow subagent templates and chain presets. Usage: /tk-bootstrap [--scope user|project] [--dry-run]",
		handler: async (args, ctx) => {
			const scope = parseScope(args);
			const dryRun = parseFlag(args, "--dry-run");
			const destinationDir =
				scope === "user"
					? path.join(os.homedir(), ".pi", "agent", "agents")
					: path.join(ctx.cwd, ".pi", "agents");

			await ensureDir(destinationDir);

			const agentFiles = await listTemplates(agentsTemplateDir, ".md");
			const chainFiles = await listTemplates(chainsTemplateDir, ".chain.md");

			const agentStats = await installTemplates(agentsTemplateDir, destinationDir, agentFiles, dryRun);
			const chainStats = await installTemplates(chainsTemplateDir, destinationDir, chainFiles, dryRun);

			const markerPath = path.join(destinationDir, ".tk-bootstrap.json");
			const marker = {
				package: "pi-tk-flow",
				scope,
				installedAt: new Date().toISOString(),
				agents: agentFiles,
				chains: chainFiles,
			};
			if (!dryRun) await fs.writeFile(markerPath, JSON.stringify(marker, null, 2) + "\n", "utf8");

			if (ctx.hasUI) {
				const mode = dryRun ? "DRY RUN" : "APPLIED";
				ctx.ui.notify(
					[
						`/tk-bootstrap (${mode})`,
						`Scope: ${scope}`,
						`Destination: ${destinationDir}`,
						`Agents -> Created: ${agentStats.created.length}, Updated: ${agentStats.updated.length}, Unchanged: ${agentStats.unchanged.length}`,
						`Chains -> Created: ${chainStats.created.length}, Updated: ${chainStats.updated.length}, Unchanged: ${chainStats.unchanged.length}`,
					].join("\n"),
					"info",
				);

				if (scope === "project") {
					ctx.ui.notify(
						"Project-scoped agents/chains installed. Ensure /tk-implement uses AGENT_SCOPE=project (or both).",
						"warning",
					);
				}
			}
		},
	});
}
