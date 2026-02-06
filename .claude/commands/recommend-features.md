# ~/.claude/commands/recommend-features.md 
 Recommend Claude Code Features

Analyze the current project and provide tailored recommendations for Claude Code features that would enhance the development workflow.

## Analysis Tasks

1. **Examine the codebase structure** - Understand the technology stack, frameworks, and development patterns
2. **Review existing configurations** - Check for package.json, Makefile, CI/CD workflows, and other automation
3. **Identify repetitive tasks** - Find common workflows that could be automated
4. **Assess integration opportunities** - Determine which external tools/APIs could benefit from MCP servers
5. **Analyze complexity patterns** - Identify multi-step workflows that could benefit from subagents

## Claude Code Feature Categories

### 1. Custom Slash Commands
**Location:** `.claude/commands/`
**File format:** Markdown (`.md`)

Project-specific commands that streamline common development tasks:
- Deployment workflows
- Testing patterns
- Code generation
- Environment management
- Database operations
- Release management
- Documentation generation

**Implementation:**
```markdown
# Command Name

Brief description

## Usage
/command-name [arg1] [arg2]

## Arguments
- arg1: description
- arg2: description

## Examples
...

## Implementation Steps
1. Step one
2. Step two
```

### 2. MCP Servers
**Location:** `.claude/mcp-servers.json`
**Purpose:** Direct integration with external tools and APIs

**Popular MCP Servers:**
- `@modelcontextprotocol/server-postgres` - PostgreSQL database access
- `@modelcontextprotocol/server-github` - GitHub API integration
- `@modelcontextprotocol/server-filesystem` - Advanced file operations
- `@modelcontextprotocol/server-memory` - Persistent conversation memory
- `@modelcontextprotocol/server-brave-search` - Web search capabilities
- `@modelcontextprotocol/server-slack` - Slack integration
- `@modelcontextprotocol/server-sequential-thinking` - Step-by-step reasoning
- Custom project-specific MCP servers

**Configuration:**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "ENV_VAR": "${ENV_VAR}"
      }
    }
  }
}
```

### 3. Hooks
**Location:** `.claude/hooks/`
**File format:** Shell scripts (`.sh`) or executables
**Trigger types:** `before_tool_call`, `after_tool_call`, `on_file_change`

Event-driven automation for:
- Pre-commit quality checks
- Post-deployment verification
- AWS profile validation
- Terraform plan review
- File operation safety checks
- User prompt enhancements

**Hook Configuration:**
```json
{
  "trigger": "before_tool_call",
  "tool_patterns": ["Bash(git commit*)", "Bash(terraform *apply*)"],
  "script": ".claude/hooks/your-hook.sh"
}
```

**Hook Script Template:**
```bash
#!/bin/bash
COMMAND="$1"

# Your validation logic here
if [[ condition ]]; then
  echo "❌ Validation failed"
  exit 1
fi

echo "✅ Validation passed"
exit 0
```

### 4. Skills
**Purpose:** Reusable capabilities for specialized domain-specific tasks

Skills are invoked using the `Skill` tool and provide specialized knowledge and workflows.

**Use cases:**
- PDF manipulation
- Excel/CSV processing
- Image processing
- Data transformation
- Code refactoring patterns
- Domain-specific operations

**Note:** Skills are typically provided via plugins/packages and require specific configuration.

### 5. Subagents (Task Tool)
**Purpose:** Launch specialized agents for complex, multi-step tasks

**Available Subagent Types:**

#### `general-purpose`
Multi-step tasks, complex research, autonomous workflows
- Access to all tools
- Best for open-ended exploration
- Can perform multiple searches and reads

#### `Explore`
Fast codebase exploration and analysis
- Quick file pattern searches (`**/*.tsx`)
- Keyword searches in code
- Codebase understanding questions
- Thoroughness levels: `quick`, `medium`, `very thorough`

#### `Plan`
Implementation planning and design
- Creates implementation plans
- Identifies dependencies
- Generates task breakdowns
- Thoroughness levels: `quick`, `medium`, `very thorough`

**When to use subagents:**
- Searching for patterns across large codebases
- Multi-step investigations (when you need multiple search attempts)
- Complex refactoring that requires understanding many files
- Generating comprehensive documentation
- Analyzing architecture and dependencies
- Tasks requiring autonomous decision-making

**When NOT to use subagents:**
- Reading specific known file paths (use Read tool)
- Searching for specific class definitions (use Glob tool)
- Searching within 2-3 known files (use Read tool)
- Simple, single-step operations

**Example subagent invocation:**
```
Task tool with:
- subagent_type: "Explore"
- description: "Find authentication flow"
- prompt: "Search the codebase for authentication-related code.
  Find login, session management, and token handling.
  Use thorough exploration."
```

### 6. Permissions Configuration
**Location:** `.claude/settings.local.json`

Control which commands run without approval:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test:*)",
      "Bash(make:*)",
      "Bash(git status)",
      "WebFetch(domain:docs.example.com)"
    ],
    "deny": [
      "Bash(rm -rf *)"
    ],
    "ask": []
  }
}
```

### 7. Advanced Features

#### Multi-Agent Workflows
Run multiple subagents in parallel for complex tasks:
```
1. Launch "Explore" agent to find all API endpoints
2. Launch "Plan" agent to design testing strategy
3. Synthesize results into comprehensive test plan
```

#### Stateful MCP Servers
Use memory MCP server for persistent context:
- Store project conventions
- Remember user preferences
- Track previous decisions
- Maintain conversation history

#### Custom MCP Server Development
Create project-specific MCP servers:
- Internal API integrations
- Custom database queries
- Proprietary tool access
- Company-specific workflows

## Recommendation Framework

For each recommendation, provide:

### Template
**Name:** Clear identifier
**Type:** command | mcp-server | hook | skill | subagent-workflow
**Priority:** 🔴 High | 🟡 Medium | 🟢 Low
**Purpose:** What problem it solves (1-2 sentences)
**Implementation:** Concrete steps or code to create it
**Example Usage:** How a developer would use it

### Evaluation Criteria

**High Priority (🔴):**
- Prevents critical errors (wrong deployments, data loss)
- Saves >30 minutes per week
- Reduces cognitive load for complex tasks
- Addresses frequent pain points

**Medium Priority (🟡):**
- Improves workflow efficiency
- Saves 10-30 minutes per week
- Enhances code quality
- Provides better integration

**Low Priority (🟢):**
- Nice-to-have improvements
- Saves <10 minutes per week
- Incremental benefits
- Exploration and learning

## Analysis Methodology

### 1. Codebase Analysis
```
- Identify project type (web, mobile, API, monorepo, etc.)
- List primary languages and frameworks
- Find existing automation (Makefile, package.json scripts)
- Identify external services (databases, APIs, cloud providers)
- Check CI/CD workflows
```

### 2. Workflow Pattern Detection
```
- Deployment patterns (multi-environment, single env, etc.)
- Testing patterns (unit, integration, e2e, contract)
- Database operations (migrations, queries, backups)
- External API usage (authentication, rate limits)
- Code generation needs
```

### 3. Integration Opportunities
```
- Services with APIs → MCP servers
- Repetitive CLI commands → Slash commands
- Safety-critical operations → Hooks
- Complex multi-step tasks → Subagent workflows
- Domain-specific operations → Skills
```

### 4. Complexity Assessment
```
- Multi-step workflows → Subagents
- Simple automations → Slash commands
- Safety checks → Hooks
- External integrations → MCP servers
```

## Output Format

Provide 5-10 high-impact recommendations structured as:

### Priority Order
1. List high priority items first
2. Group by type (commands, hooks, MCP servers, subagents)
3. Include implementation effort estimate
4. Show expected impact/time savings

### Implementation Guide
For each recommendation:
1. Show exact file paths
2. Provide complete code/configuration
3. Include setup instructions
4. Give usage examples
5. List prerequisites (env vars, packages, etc.)

### Summary Matrix
```
| Feature | Priority | Effort | Impact | Type |
|---------|----------|--------|--------|------|
| ... | 🔴 High | 30 min | Prevents incidents | Hook |
```

## Advanced Recommendations

### When to Recommend Subagents

**Good use cases:**
- "Find all database queries across the entire codebase"
- "Analyze authentication flow spanning multiple services"
- "Generate migration guide for framework upgrade"
- "Create comprehensive API documentation from code"
- "Refactor feature across 20+ files"

**Poor use cases:**
- "Read the config file at path/to/config.json" (use Read)
- "Find class UserService" (use Glob)
- "Search for TODO comments in 3 files" (use Grep)

### When to Recommend MCP Servers

**Indicators:**
- Frequent API calls to same service
- Database queries in conversation
- Need for external tool integration
- Persistent state requirements
- Real-time data access needs

### When to Recommend Hooks

**Indicators:**
- Critical safety operations (deployments, deletions)
- Repeated validation patterns
- Pre-flight checks needed
- Environment-specific constraints
- Compliance requirements

## Focus Areas

Prioritize recommendations that:
- **Save time** on frequently-performed tasks (>weekly)
- **Reduce risk** of errors (especially in deployment/infrastructure)
- **Improve quality** through automated checks and testing
- **Enhance integration** with external services and tools
- **Align with patterns** already established in the project
- **Enable autonomy** through subagents for complex research
- **Provide safety** through hooks for critical operations
- **Streamline workflows** through slash commands for common tasks

## Deliverable

After analyzing the project:
1. Provide 5-10 specific, actionable recommendations
2. Include complete implementation code
3. Show concrete usage examples
4. Estimate time savings and impact
5. Suggest implementation order
6. Include any prerequisites (API keys, packages, etc.)

Focus on features that can be implemented immediately and provide measurable value.