---
name: "github-deploy"
description: "Automates GitHub deployment workflow: authentication, git add/commit/pull/push with conflict resolution. Invoke when user wants to push code to GitHub repository."
---

# GitHub Deploy

This skill automates the complete GitHub deployment workflow, from authentication to pushing code changes.

## When to Invoke

Invoke this skill when the user wants to:
- Push local code changes to a GitHub repository
- Set up GitHub deployment for the first time
- Commit and push code in one operation
- Handle GitHub authentication and repository management

## Prerequisites

- Git must be installed and configured
- GitHub Personal Access Token (PAT) with appropriate permissions (repo scope)
- The project must be a git repository

## Configuration

The skill uses a configuration file `.github-deploy.json` in the project root directory. This file should be added to `.gitignore` to avoid committing sensitive information.

**Configuration file structure:**
```json
{
  "github_token": "your_github_pat_here",
  "repository_url": "https://github.com/username/repo.git",
  "branch": "current_branch_name"
}
```

**Important:** The `.github-deploy.json` file must be added to `.gitignore` to prevent committing sensitive credentials.

## Workflow Steps

### Step 1: Authentication Check
- Check if `.github-deploy.json` exists in the project root
- If not exists, prompt user to provide:
  - GitHub Personal Access Token (PAT)
  - GitHub repository URL (e.g., `https://github.com/username/repo.git`)
- Save credentials to `.github-deploy.json`
- Verify the token is valid by testing GitHub API access

### Step 2: Repository Setup
- Check if the project is already a git repository
- If not, initialize: `git init`
- Configure git user if not set
- Set up remote repository if not configured
- Verify remote URL matches the configuration

### Step 3: Stage Changes
- Execute: `git add .`
- Execute: `git status` to show what will be committed
- Display the list of changed files to the user

### Step 4: Commit Changes
- Analyze the changes using `git diff --cached`
- Generate a Chinese commit message summarizing the modifications
- Execute: `git commit -m '<commit_message>'`
- Display the commit hash and message

### Step 5: Pull with Rebase
- Execute: `git pull --rebase origin <current_branch>`
- Handle conflicts:
  - If no conflicts: proceed to push
  - If conflicts occur:
    - Display conflict information
    - Attempt automatic conflict resolution if possible
    - If conflicts cannot be resolved automatically:
      - Pause and inform user
      - Provide conflict resolution guidance:
        ```
        冲突解决指导：
        1. 查看冲突文件：git status
        2. 编辑冲突文件，解决冲突标记（<<<<<<<, =======, >>>>>>>）
        3. 标记冲突已解决：git add <conflicted_files>
        4. 继续rebase：git rebase --continue
        5. 如果需要放弃：git rebase --abort
        ```
      - Wait for user to manually resolve conflicts
      - After user confirms resolution, proceed with push

### Step 6: Push Changes
- Execute: `git push origin <current_branch>`
- Display push result
- Show the GitHub repository URL for verification

### Step 7: Summary and Verification
- Print a summary of the entire process
- Display:
  - Files committed
  - Commit message
  - Branch pushed
  - Repository URL
  - Any warnings or errors encountered
- Provide link to view the commit on GitHub

## Error Handling

- **Authentication errors**: Prompt user to update GitHub token
- **Network errors**: Retry up to 3 times with exponential backoff
- **Merge conflicts**: Follow the conflict resolution workflow in Step 5
- **Permission errors**: Inform user about required repository permissions
- **Invalid repository URL**: Prompt user to correct the URL

## Security Considerations

- Never log or display the full GitHub token
- Always add `.github-deploy.json` to `.gitignore`
- Warn user if the config file is about to be committed
- Use HTTPS for repository URLs with token authentication
- Token should have minimum required permissions (repo scope)

## Example Usage

**First-time setup:**
```
User: "帮我部署代码到 GitHub"
Skill: "检测到首次使用，请提供 GitHub Personal Access Token 和仓库地址"
User: "token: ghp_xxxx, repo: https://github.com/user/project.git"
Skill: "配置已保存，开始部署流程..."
```

**Subsequent deployments:**
```
User: "提交代码到 GitHub"
Skill: "读取配置文件，执行 git add/commit/pull/push..."
```

## Output Format

The skill should provide clear, step-by-step output in Chinese:

```
[步骤 1/7] 检查认证配置...
✓ 配置文件已找到

[步骤 2/7] 准备提交代码...
✓ 已暂存 5 个文件

[步骤 3/7] 生成提交信息...
提交信息: 修复用户登录接口的bug，优化数据库查询性能

[步骤 4/7] 执行提交...
✓ 提交成功: abc1234

[步骤 5/7] 拉取远程更新...
✓ 已同步最新代码

[步骤 6/7] 推送到 GitHub...
✓ 推送成功

[步骤 7/7] 部署完成！
仓库: https://github.com/user/project.git
分支: main
提交: abc1234
查看: https://github.com/user/project/commit/abc1234
```

## Additional Notes

- Always work with the current branch (detect via `git branch --show-current`)
- If the current branch doesn't exist on remote, create it with `git push -u origin <branch>`
- Support force push only with explicit user confirmation
- Provide rollback instructions if deployment fails
- Check for large files and warn user before committing