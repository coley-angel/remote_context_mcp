# Terraform Development Workflow

## Overview
This workflow ensures safe and reliable infrastructure changes using Terraform.

## Setup

### 1. Install Required Tools
```bash
# Install Terraform
brew install terraform  # macOS
# or
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip

# Install terraform-docs (optional, for documentation)
brew install terraform-docs

# Install tflint (optional, for linting)
brew install tflint

# Install checkov (optional, for security scanning)
pip install checkov
```

### 2. Configure Backend
```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state"
    key            = "env/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### 3. Environment Variables
```bash
# AWS credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_REGION="us-east-1"

# Or use AWS profile
export AWS_PROFILE="your-profile"

# Terraform variables (optional)
export TF_VAR_environment="dev"
export TF_VAR_region="us-east-1"
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b terraform/add-rds-instance
```

### 2. Initialize Terraform
```bash
cd terraform/

# Initialize providers and backend
terraform init

# Select or create workspace
terraform workspace list
terraform workspace select dev
# or
terraform workspace new dev
```

### 3. Write Terraform Code
```hcl
# main.tf
resource "aws_db_instance" "main" {
  identifier     = "${var.environment}-database"
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = var.db_instance_class
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = var.environment == "prod" ? 7 : 1
  skip_final_snapshot     = var.environment != "prod"
  final_snapshot_identifier = "${var.environment}-final-snapshot"
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.environment}-database"
    }
  )
}
```

### 4. Format and Validate
```bash
# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Optional: Run linter
tflint

# Optional: Security scan
checkov -d .
```

### 5. Plan Changes
```bash
# Create plan
terraform plan -out=tfplan

# Review plan carefully
# - Resources to be created (+)
# - Resources to be modified (~)
# - Resources to be destroyed (-)

# Save plan output for review
terraform show tfplan > plan.txt
```

### 6. Review Checklist
- [ ] All resources have appropriate tags
- [ ] Sensitive data not hardcoded
- [ ] Encryption enabled where applicable
- [ ] Backup retention configured
- [ ] IAM permissions follow least privilege
- [ ] No resources will be unnecessarily destroyed
- [ ] Cost implications understood
- [ ] Plan output reviewed line by line

## Applying Changes

### Development Environment
```bash
# Apply immediately (dev only)
terraform apply tfplan

# Or interactive apply
terraform apply
```

### Staging Environment
```bash
# Switch to staging workspace
terraform workspace select staging

# Plan with staging variables
terraform plan -var-file=staging.tfvars -out=tfplan

# Review plan with team member
# Apply after approval
terraform apply tfplan
```

### Production Environment
```bash
# PRODUCTION CHANGES REQUIRE:
# 1. Peer review of code
# 2. Successful apply in staging
# 3. Change request approval
# 4. Maintenance window (if applicable)

# Switch to prod workspace
terraform workspace select prod

# Plan with production variables
terraform plan -var-file=prod.tfvars -out=tfplan

# Save and review plan
terraform show tfplan > prod-plan.txt

# Share plan with team for review
# Wait for approvals

# Apply during maintenance window
terraform apply tfplan

# Monitor resources after apply
```

## Testing Infrastructure

### Validate Resources
```bash
# Verify resources were created
terraform show

# Check specific resource
terraform state show aws_db_instance.main

# List all resources
terraform state list

# Refresh state
terraform refresh
```

### Application Testing
```bash
# Get outputs for testing
terraform output

# Example: Test database connectivity
DB_HOST=$(terraform output -raw db_endpoint)
psql -h $DB_HOST -U admin -d myapp
```

### Smoke Tests
```bash
# Test API endpoints
curl https://api.example.com/health

# Verify DNS resolution
nslookup example.com

# Check load balancer
curl https://lb.example.com
```

## Common Operations

### Viewing Resources
```bash
# Show current state
terraform show

# Show specific resource
terraform state show aws_instance.web

# List all resources
terraform state list

# Show outputs
terraform output
```

### Modifying State
```bash
# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Move resource in state
terraform state mv aws_instance.old aws_instance.new

# Remove resource from state (doesn't delete actual resource)
terraform state rm aws_instance.temp

# Pull state to local file
terraform state pull > terraform.tfstate.backup
```

### Targeting Specific Resources
```bash
# Plan only for specific resource
terraform plan -target=aws_instance.web

# Apply only to specific resource
terraform apply -target=aws_instance.web

# Destroy only specific resource
terraform destroy -target=aws_s3_bucket.old_bucket
```

### Working with Variables
```bash
# Use variable file
terraform plan -var-file=production.tfvars

# Override specific variable
terraform plan -var="instance_count=5"

# Multiple variable files
terraform plan -var-file=common.tfvars -var-file=prod.tfvars
```

## Rollback Procedures

### Revert to Previous State
```bash
# Option 1: Revert code changes
git revert <commit-hash>
terraform plan
terraform apply

# Option 2: Import from backup
terraform state push terraform.tfstate.backup

# Option 3: Use version control
aws s3 cp s3://terraform-state/env/terraform.tfstate.backup ./
terraform state push terraform.tfstate.backup
```

### Emergency Resource Recreation
```bash
# Taint resource (marks for recreation)
terraform taint aws_instance.web

# Apply to recreate
terraform apply

# Untaint if needed
terraform untaint aws_instance.web
```

## Troubleshooting

### State Lock Issues
```bash
# If state is locked
terraform force-unlock <lock-id>

# Check lock status in DynamoDB
aws dynamodb get-item \
  --table-name terraform-locks \
  --key '{"LockID": {"S": "terraform-state/env/terraform.tfstate"}}'
```

### Provider Issues
```bash
# Reinitialize providers
rm -rf .terraform/
terraform init

# Upgrade providers
terraform init -upgrade

# Check provider versions
terraform version
```

### Import Existing Resources
```bash
# Find resource ID
aws ec2 describe-instances --filters "Name=tag:Name,Values=my-instance"

# Import into Terraform
terraform import aws_instance.main i-1234567890abcdef0

# Verify import
terraform plan  # Should show no changes
```

## Best Practices

### Before Committing
```bash
# Run pre-commit checks
terraform fmt -check -recursive
terraform validate
terraform plan -detailed-exitcode

# Generate documentation
terraform-docs markdown . > README.md
```

### Pull Request Requirements
- [ ] Code formatted (`terraform fmt`)
- [ ] Validation passes (`terraform validate`)
- [ ] Plan output included in PR description
- [ ] No sensitive data in code
- [ ] All resources tagged
- [ ] Documentation updated
- [ ] Tested in dev/staging

### Collaboration
```bash
# Lock state during critical operations
# (automatically happens with apply/destroy)

# Use workspaces for environments
terraform workspace select dev

# Share plan files for review
terraform show tfplan > plan-for-review.txt

# Use version control for all changes
git add .
git commit -m "terraform: Add RDS instance for prod"
```

## Disaster Recovery

### State Backup
```bash
# Backup state file
terraform state pull > backup-$(date +%Y%m%d-%H%M%S).tfstate

# Automated backup (add to CI/CD)
#!/bin/bash
terraform state pull > terraform.tfstate.backup
aws s3 cp terraform.tfstate.backup \
  s3://backup-bucket/terraform-state/$(date +%Y%m%d-%H%M%S)/
```

### State Recovery
```bash
# List state versions (S3 versioning enabled)
aws s3api list-object-versions \
  --bucket terraform-state \
  --prefix env/terraform.tfstate

# Download specific version
aws s3api get-object \
  --bucket terraform-state \
  --key env/terraform.tfstate \
  --version-id <version-id> \
  terraform.tfstate.recovered

# Push recovered state
terraform state push terraform.tfstate.recovered
```

## Automation

### CI/CD Pipeline
```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        
      - name: Terraform Format
        run: terraform fmt -check -recursive
        
      - name: Terraform Init
        run: terraform init
        
      - name: Terraform Validate
        run: terraform validate
        
      - name: Terraform Plan
        if: github.event_name == 'pull_request'
        run: |
          terraform plan -no-color > plan.txt
          cat plan.txt
          
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('plan.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `#### Terraform Plan\n\`\`\`\n${plan}\n\`\`\``
            });
```

### Makefile for Common Tasks
```makefile
.PHONY: init plan apply destroy fmt validate

init:
	terraform init

plan:
	terraform plan -out=tfplan

apply:
	terraform apply tfplan

destroy:
	terraform destroy

fmt:
	terraform fmt -recursive

validate: fmt
	terraform validate
	tflint
	checkov -d .

docs:
	terraform-docs markdown . > README.md
```

## Security Checklist

- [ ] No hardcoded credentials
- [ ] Encryption enabled for data at rest
- [ ] Encryption enabled for data in transit
- [ ] Security groups follow least privilege
- [ ] IAM roles use least privilege
- [ ] Logging and monitoring enabled
- [ ] Backup and retention configured
- [ ] Tags include Owner and Environment
- [ ] State file encrypted
- [ ] State locking enabled

## Cost Management

### Estimate Costs
```bash
# Use Infracost (optional tool)
infracost breakdown --path .

# Review resource types
terraform plan | grep "will be created"

# Check for expensive resources
# - Large EC2 instances
# - High IOPS storage
# - Data transfer charges
# - NAT Gateways
```

### Cost Optimization
- Use appropriate instance sizes
- Enable auto-scaling
- Use Reserved Instances for predictable workloads
- Implement resource tagging for cost allocation
- Set up budget alerts
- Review and clean up unused resources

---

**Remember**: Infrastructure changes can have significant impact. Always plan carefully, 
test thoroughly, and review with the team before applying to production.
