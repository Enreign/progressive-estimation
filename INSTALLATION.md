# Installation Guide

Progressive Estimation works with any AI coding client that supports custom
instructions. This guide covers installation for each major client.

> [!NOTE]
> **Progressive loading** (only loading what's needed per phase) is fully
> supported in Claude Code, Cursor, and GitHub Copilot. For other clients,
> you may need to consolidate the skill into a single file or accept that
> all content loads at once. See the notes per client below.

---

## Claude Code

**Full progressive loading support.** The skill was designed for Claude Code
and works best here — files load on demand per phase.

```bash
# Clone into your skills directory
git clone https://github.com/Enreign/agent-skills.git ~/.claude/skills/agent-skills
```

That's it. The skill auto-triggers when you ask for estimates. You can also
invoke it explicitly with `/progressive-estimation`.

**How it works:** Claude Code reads `SKILL.md` as the entry point and loads
reference files on demand as the estimation workflow progresses through phases.

---

## Cursor

**Supports conditional loading via glob and agent-decided rules.**

### Option A: Agent-Decided Rule (Recommended)

Create a single rule file that Cursor loads when estimation is relevant:

```bash
# Create the rules directory
mkdir -p .cursor/rules

# Copy the skill file
cp path/to/progressive-estimation/SKILL.md .cursor/rules/progressive-estimation.mdc
```

Add this frontmatter to the top of the `.mdc` file:

```yaml
---
description: "Use when the user asks for time estimates, effort sizing, story points, or estimation of development tasks"
alwaysApply: false
---
```

### Option B: Full Skill with References

For the complete skill with all reference files:

```bash
# Copy the entire skill into your project
cp -r path/to/progressive-estimation .cursor/rules/progressive-estimation
```

Create `.cursor/rules/progressive-estimation.mdc`:

```yaml
---
description: "Use when the user asks for time estimates, effort sizing, or estimation"
alwaysApply: false
---
For estimation tasks, read and follow the workflow in:
@.cursor/rules/progressive-estimation/SKILL.md

Reference files are in @.cursor/rules/progressive-estimation/references/
```

> [!NOTE]
> Cursor does not have a documented character limit per rule, but keep
> the main rule file concise and let `@file` references pull in details.

---

## Windsurf

**Partial progressive loading via Model Decision mode.**

```bash
# Create the rules directory
mkdir -p .windsurf/rules

# Copy the main skill file
cp path/to/progressive-estimation/SKILL.md .windsurf/rules/progressive-estimation.md
```

> [!WARNING]
> Windsurf limits individual rule files to **6,000 characters** and combined
> rules to **12,000 characters total**. The full `SKILL.md` fits within this
> limit, but reference files will need to be loaded via chat context rather
> than as rules.

To use the full skill, keep `SKILL.md` as the rule and add reference files
to your project directory. Ask the AI to read them when needed:

```
Read references/formulas.md and estimate this task: ...
```

---

## GitHub Copilot

**Supports path-specific progressive loading.**

### Option A: Repository-Wide Instructions

```bash
# Create the instructions directory
mkdir -p .github/instructions

# Copy the main skill file
cp path/to/progressive-estimation/SKILL.md .github/copilot-instructions.md
```

Or for conditional loading:

```bash
cp path/to/progressive-estimation/SKILL.md .github/instructions/estimation.instructions.md
```

Add frontmatter for conditional activation:

```yaml
---
applyTo: "**/*"
---
```

### Option B: Full Skill with References

Copy the entire skill into your repo and reference it:

```bash
cp -r path/to/progressive-estimation ./progressive-estimation
```

In `.github/copilot-instructions.md`, add:

```markdown
For estimation tasks, follow the workflow in [SKILL.md](progressive-estimation/SKILL.md).
Reference files are in [references/](progressive-estimation/references/).
```

> [!NOTE]
> GitHub Copilot supports `#file:path/to/file` syntax to reference
> specific files within instruction files.

---

## Cline (VS Code)

**No progressive loading — all rules load together.**

### Option A: Single File

```bash
# Copy to project root
cp path/to/progressive-estimation/SKILL.md .clinerules
```

### Option B: Directory with Multiple Files

```bash
# Create rules directory
mkdir -p .clinerules

# Copy skill and key references
cp path/to/progressive-estimation/SKILL.md .clinerules/01-estimation-workflow.md
cp path/to/progressive-estimation/references/formulas.md .clinerules/02-estimation-formulas.md
cp path/to/progressive-estimation/references/questionnaire.md .clinerules/03-estimation-questionnaire.md
```

> [!NOTE]
> All files in `.clinerules/` load together. Number-prefix the files to
> control loading order. Only include the references you use most often
> to avoid consuming too much context.

### Option C: Global Custom Instructions

In VS Code: Settings > Extensions > Cline > Custom Instructions

Paste the contents of `SKILL.md` into the text field.

---

## Aider

**No progressive loading — all files load at session start.**

### Option A: Convention File

```bash
# Copy to project root
cp path/to/progressive-estimation/SKILL.md CONVENTIONS.md
```

Add to `.aider.conf.yml`:

```yaml
read: CONVENTIONS.md
```

### Option B: Multiple Reference Files

```bash
# Copy the skill into your project
cp -r path/to/progressive-estimation ./estimation
```

Add to `.aider.conf.yml`:

```yaml
read:
  - estimation/SKILL.md
  - estimation/references/formulas.md
  - estimation/references/questionnaire.md
```

> [!WARNING]
> All `read:` files load into context at session start and stay there.
> Only include files you'll actively use to preserve context window space.
> The full skill (~2,000 lines across all files) may consume significant
> context in smaller models.

### Option C: On-Demand Loading

Start with just the workflow:

```yaml
read: estimation/SKILL.md
```

Then load references as needed during the session:

```
/read estimation/references/formulas.md
```

---

## Continue.dev

**No progressive loading — rules go into every system message.**

Add to `~/.continue/config.yaml`:

```yaml
rules:
  - uses: file:///absolute/path/to/progressive-estimation/SKILL.md
```

Or for a project-specific setup, create `.continuerc.json`:

```json
{
  "rules": [
    {
      "uses": "file://./progressive-estimation/SKILL.md"
    }
  ]
}
```

> [!NOTE]
> Rules are included in every request's system message. Keep it to
> `SKILL.md` only and instruct the model to read reference files
> from disk when needed during the estimation workflow.

---

## ChatGPT (Projects)

**No file-based config — everything is in the UI.**

1. Create a new Project in ChatGPT
2. Open **Project Instructions**
3. Paste the contents of `SKILL.md` into the instructions field
4. Upload reference files to the Project:
   - `references/formulas.md`
   - `references/questionnaire.md`
   - `references/frameworks.md`
   - `references/output-schema.md`
   - `references/calibration.md`

> [!WARNING]
> Project instructions have a **1,500 character limit**. You'll need a
> condensed version of `SKILL.md` for the instructions field. Upload the
> full `SKILL.md` as a project file instead, and use a short instruction
> like: *"For estimation tasks, follow the workflow in the uploaded SKILL.md
> file and reference the uploaded formulas, questionnaire, and other files
> as needed."*

---

## Gemini Code Assist

**No progressive loading — style guide loads with every request.**

```bash
# Create the Gemini config directory
mkdir -p .gemini

# Copy as style guide
cp path/to/progressive-estimation/SKILL.md .gemini/styleguide.md
```

> [!NOTE]
> Gemini Code Assist treats `styleguide.md` as a general coding style
> guide. For estimation-specific use, prepend a note: *"This style guide
> includes an estimation workflow. Apply it when the user asks for
> estimates, sizing, or effort assessment."*

For reference files, place them in the project and ask Gemini to read
them during estimation conversations.

---

## Consolidated Single-File Version

For clients with strict character limits or no multi-file support, you can
ask Claude Code to generate a consolidated version:

```
Combine SKILL.md and the key formulas into a single file under 6000 characters
```

This produces a condensed version suitable for Windsurf, ChatGPT instructions,
or any client with tight limits.

---

## Comparison

| Client | Install Method | Progressive Loading | Limits | Effort |
|--------|---------------|-------------------|--------|--------|
| **Claude Code** | `git clone` to skills dir | Full | 2% context for descriptions | Easiest |
| **Cursor** | `.cursor/rules/*.mdc` | Yes (agent-decided) | No documented limit | Easy |
| **GitHub Copilot** | `.github/instructions/` | Yes (path-specific) | No documented limit | Easy |
| **Windsurf** | `.windsurf/rules/*.md` | Partial | 6K/file, 12K total | Moderate |
| **Cline** | `.clinerules/` directory | No | No documented limit | Easy |
| **Aider** | `read:` in `.aider.conf.yml` | No (on-demand via `/read`) | Context window | Moderate |
| **Continue.dev** | `rules:` in `config.yaml` | No | Context window | Easy |
| **ChatGPT** | Project UI + file uploads | No | 1,500 chars instructions | Manual |
| **Gemini** | `.gemini/styleguide.md` | No | No documented limit | Easy |
