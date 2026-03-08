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
	skipped: string[];
};

type InstallOptions = {
	dryRun: boolean;
	noOverwrite: boolean;
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

function parseCopyOptions(args: string): { copyPrompts: boolean; copySkills: boolean } {
	const copyAll = parseFlag(args, "--copy-all") || parseFlag(args, "--materialize");
	return {
		copyPrompts: copyAll || parseFlag(args, "--copy-prompts"),
		copySkills: copyAll || parseFlag(args, "--copy-skills"),
	};
}

async function ensureDir(dir: string): Promise<void> {
	await fs.mkdir(dir, { recursive: true });
}

async function ensureParentDir(filePath: string): Promise<void> {
	await ensureDir(path.dirname(filePath));
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

async function pathExists(targetPath: string): Promise<boolean> {
	try {
		await fs.access(targetPath);
		return true;
	} catch {
		return false;
	}
}

async function listFilesRecursive(rootDir: string): Promise<string[]> {
	const files: string[] = [];

	if (!(await pathExists(rootDir))) return files;

	async function walk(currentDir: string, relativeDir: string): Promise<void> {
		const entries = await fs.readdir(currentDir, { withFileTypes: true });
		for (const entry of entries) {
			const relativePath = relativeDir ? path.join(relativeDir, entry.name) : entry.name;
			const absolutePath = path.join(currentDir, entry.name);
			if (entry.isDirectory()) {
				await walk(absolutePath, relativePath);
			} else if (entry.isFile()) {
				files.push(relativePath);
			}
		}
	}

	await walk(rootDir, "");
	files.sort();
	return files;
}

async function installFiles(
	srcDir: string,
	dstDir: string,
	fileNames: string[],
	options: InstallOptions,
): Promise<InstallStats> {
	const created: string[] = [];
	const updated: string[] = [];
	const unchanged: string[] = [];
	const skipped: string[] = [];

	for (const fileName of fileNames) {
		const src = path.join(srcDir, fileName);
		const dst = path.join(dstDir, fileName);
		const srcContent = await fs.readFile(src, "utf8");
		const dstContent = await readIfExists(dst);

		if (dstContent === null) {
			created.push(fileName);
			if (!options.dryRun) {
				await ensureParentDir(dst);
				await fs.writeFile(dst, srcContent, "utf8");
			}
			continue;
		}

		if (dstContent !== srcContent) {
			if (options.noOverwrite) {
				skipped.push(fileName);
				continue;
			}
			updated.push(fileName);
			if (!options.dryRun) {
				await ensureParentDir(dst);
				await fs.writeFile(dst, srcContent, "utf8");
			}
		} else {
			unchanged.push(fileName);
		}
	}

	return { created, updated, unchanged, skipped };
}

function statsLine(label: string, stats: InstallStats): string {
	return `${label} -> Created: ${stats.created.length}, Updated: ${stats.updated.length}, Unchanged: ${stats.unchanged.length}, Skipped: ${stats.skipped.length}`;
}

export default function tfBootstrapExtension(pi: ExtensionAPI) {
	const __filename = fileURLToPath(import.meta.url);
	const __dirname = path.dirname(__filename);
	const agentsTemplateDir = path.resolve(__dirname, "..", "assets", "agents");
	const chainsTemplateDir = path.resolve(__dirname, "..", "assets", "chains");
	const promptsTemplateDir = path.resolve(__dirname, "..", "prompts");
	const skillsTemplateDir = path.resolve(__dirname, "..", "skills");

	pi.registerCommand("tf-bootstrap", {
		description:
			"Install/update tf workflow templates. Usage: /tf-bootstrap [--scope user|project] [--dry-run] [--copy-prompts] [--copy-skills] [--copy-all|--materialize] [--no-overwrite]",
		handler: async (args, ctx) => {
			const scope = parseScope(args);
			const dryRun = parseFlag(args, "--dry-run");
			const noOverwrite = parseFlag(args, "--no-overwrite");
			const copyOptions = parseCopyOptions(args);

			const rootDestinationDir =
				scope === "user" ? path.join(os.homedir(), ".pi", "agent") : path.join(ctx.cwd, ".pi");
			const agentsDestinationDir = path.join(rootDestinationDir, "agents");
			const promptsDestinationDir = path.join(rootDestinationDir, "prompts");
			const skillsDestinationDir = path.join(rootDestinationDir, "skills");
			const installOptions: InstallOptions = { dryRun, noOverwrite };

			await ensureDir(agentsDestinationDir);

			const agentFiles = await listTemplates(agentsTemplateDir, ".md");
			const chainFiles = await listTemplates(chainsTemplateDir, ".chain.md");

			const agentStats = await installFiles(agentsTemplateDir, agentsDestinationDir, agentFiles, installOptions);
			const chainStats = await installFiles(chainsTemplateDir, agentsDestinationDir, chainFiles, installOptions);

			let promptStats: InstallStats | null = null;
			if (copyOptions.copyPrompts) {
				await ensureDir(promptsDestinationDir);
				const promptFiles = (await listFilesRecursive(promptsTemplateDir)).filter((file) => file.endsWith(".md"));
				promptStats = await installFiles(promptsTemplateDir, promptsDestinationDir, promptFiles, installOptions);
			}

			let skillStats: InstallStats | null = null;
			const hasBundledSkills = await pathExists(skillsTemplateDir);
			if (copyOptions.copySkills && hasBundledSkills) {
				await ensureDir(skillsDestinationDir);
				const skillFiles = await listFilesRecursive(skillsTemplateDir);
				skillStats = await installFiles(skillsTemplateDir, skillsDestinationDir, skillFiles, installOptions);
			}

			const markerPath = path.join(agentsDestinationDir, ".tf-bootstrap.json");
			const marker = {
				package: "pi-tf-flow",
				scope,
				installedAt: new Date().toISOString(),
				agentsDir: agentsDestinationDir,
				agents: agentFiles,
				chains: chainFiles,
				copied: {
					prompts: copyOptions.copyPrompts,
					skills: copyOptions.copySkills && hasBundledSkills,
				},
				noOverwrite,
				promptsDir: copyOptions.copyPrompts ? promptsDestinationDir : null,
				skillsDir: copyOptions.copySkills && hasBundledSkills ? skillsDestinationDir : null,
			};
			if (!dryRun) await fs.writeFile(markerPath, JSON.stringify(marker, null, 2) + "\n", "utf8");

			if (ctx.hasUI) {
				const mode = dryRun ? "DRY RUN" : "APPLIED";
				const lines = [
					`/tf-bootstrap (${mode})`,
					`Scope: ${scope}`,
					`Overwrite mode: ${noOverwrite ? "no-overwrite (changed files preserved)" : "overwrite changed files"}`,
					`Root destination: ${rootDestinationDir}`,
					`Agents/chains destination: ${agentsDestinationDir}`,
					statsLine("Agents", agentStats),
					statsLine("Chains", chainStats),
				];

				if (promptStats) lines.push(statsLine(`Prompts (${promptsDestinationDir})`, promptStats));
				else lines.push("Prompts -> skipped (use --copy-prompts or --copy-all)");

				if (skillStats) lines.push(statsLine(`Skills (${skillsDestinationDir})`, skillStats));
				else if (copyOptions.copySkills && !hasBundledSkills) lines.push("Skills -> no bundled skills shipped in this package");
				else lines.push("Skills -> skipped (use --copy-skills or --copy-all)");

				ctx.ui.notify(lines.join("\n"), "info");

				if (scope === "project") {
					ctx.ui.notify(
						"Project-scoped templates installed. Ensure /tf-implement AGENT_SCOPE resolves to project when using .pi/agents/.tf-bootstrap.json.",
						"warning",
					);
				}
			}
		},
	});
}
