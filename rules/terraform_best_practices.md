---
trigger: always_on
glob: *.{tf,tfvars}
description: Terraform best practices and standards
---

# Terraform Best Practices

## Project Structure

### Standard Layout
```
terraform/
├── main.tf           # Main configuration
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider versions
├── terraform.tfvars  # Variable values (gitignored)
├── backend.tf        # Remote state config
├── modules/          # Local modules
│   ├── networking/
│   ├── compute/
│   └── database/
└── environments/     # Environment-specific configs
    ├── dev/
    ├── staging/
    └── prod/
```

### File Organization
- Keep related resources together
- Use modules for reusable components
- One resource type per file for large projects
- Separate data sources from resources

## Naming Conventions

### Resources
```hcl
# Use descriptive names
resource "aws_instance" "web_server" {  # Good
  # ...
}

resource "aws_instance" "server1" {     # Avoid
  # ...
}

# Use underscores, not hyphens
resource "aws_s3_bucket" "data_bucket" { # Good
}
```

### Variables
```hcl
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}
```

### Modules
```hcl
module "vpc" {
  source = "./modules/networking"
  
  environment = var.environment
  cidr_block  = var.vpc_cidr_block
}
```

## Variable Management

### Always Define Types
```hcl
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}
```

### Use Validation
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  
  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Only t3 instance types are allowed."
  }
}
```

### Sensitive Variables
```hcl
variable "database_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}
```

## Resource Configuration

### Use Dynamic Blocks
```hcl
resource "aws_security_group" "main" {
  name   = "${var.environment}-sg"
  vpc_id = aws_vpc.main.id
  
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

### Lifecycle Rules
```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  
  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true  # For critical resources
    ignore_changes        = [
      ami,  # Ignore AMI updates
      user_data,
    ]
  }
}
```

### Tags
```hcl
locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = var.project_name
    Owner       = var.owner
  }
}

resource "aws_instance" "web" {
  # ...
  
  tags = merge(
    local.common_tags,
    {
      Name = "${var.environment}-web-server"
      Role = "web"
    }
  )
}
```

## State Management

### Remote Backend
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State Locking
- Always use state locking
- Use DynamoDB for AWS S3 backend
- Never commit tfstate files
- Use workspace for multiple environments

### Workspaces
```bash
# Create workspace
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select dev

# Use in configuration
resource "aws_instance" "web" {
  count = terraform.workspace == "prod" ? 3 : 1
  # ...
}
```

## Modules

### Module Structure
```
modules/vpc/
├── main.tf
├── variables.tf
├── outputs.tf
├── README.md
└── versions.tf
```

### Module Best Practices
```hcl
# modules/networking/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-vpc"
    }
  )
}

# modules/networking/variables.tf
variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

# modules/networking/outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}
```

## Data Sources

### Use Data Sources for Existing Resources
```hcl
# Get latest AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Get existing VPC
data "aws_vpc" "main" {
  tags = {
    Name = "main-vpc"
  }
}

# Use in resources
resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  vpc_id        = data.aws_vpc.main.id
  # ...
}
```

## Security Best Practices

### Sensitive Data
```hcl
# NEVER hardcode secrets
# BAD
resource "aws_db_instance" "main" {
  password = "hardcodedpassword123"  # DON'T DO THIS
}

# GOOD - Use variables
resource "aws_db_instance" "main" {
  password = var.db_password
}

# Or use AWS Secrets Manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/db/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

### IAM Policies
```hcl
# Use least privilege
data "aws_iam_policy_document" "s3_read" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.data.arn,
      "${aws_s3_bucket.data.arn}/*",
    ]
  }
}

resource "aws_iam_policy" "s3_read" {
  name   = "${var.environment}-s3-read-policy"
  policy = data.aws_iam_policy_document.s3_read.json
}
```

### Encryption
```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${var.environment}-data-bucket"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

## Version Constraints

### Provider Versions
```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}
```

### Module Versions
```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  # ...
}
```

## Terraform Commands

### Development Workflow
```bash
# Initialize
terraform init

# Format code
terraform fmt -recursive

# Validate configuration
terraform validate

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Destroy (careful!)
terraform destroy
```

### Advanced Commands
```bash
# Target specific resource
terraform plan -target=aws_instance.web

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Taint resource (force recreation)
terraform taint aws_instance.web

# Show state
terraform show

# List resources
terraform state list

# Move resource in state
terraform state mv aws_instance.old aws_instance.new
```

## Testing

### Pre-commit Checks
```bash
#!/bin/bash
# Run before committing

terraform fmt -check -recursive || exit 1
terraform validate || exit 1
terraform plan -detailed-exitcode || exit 1
```

### Validation
```hcl
# Use validation blocks
variable "allowed_regions" {
  type = list(string)
  
  validation {
    condition     = alltrue([for r in var.allowed_regions : contains(["us-east-1", "us-west-2", "eu-west-1"], r)])
    error_message = "Only specific regions are allowed."
  }
}
```

## Documentation

### Module Documentation
```hcl
# modules/vpc/README.md
```markdown
# VPC Module

Creates a VPC with subnets and networking components.

## Usage

```hcl
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  environment = "prod"
  availability_zones = ["us-east-1a", "us-east-1b"]
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| cidr_block | CIDR block for VPC | string | - | yes |
| environment | Environment name | string | - | yes |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | ID of the VPC |
| subnet_ids | List of subnet IDs |
```

### Inline Comments
```hcl
# Create VPC with DNS support enabled
# This is required for private hosted zones
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true  # Required for RDS
  enable_dns_support   = true
}
```

## Common Patterns

### Count vs For_Each
```hcl
# Use count for simple repetition
resource "aws_instance" "web" {
  count = var.instance_count
  
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  
  tags = {
    Name = "${var.environment}-web-${count.index}"
  }
}

# Use for_each for named resources
resource "aws_s3_bucket" "buckets" {
  for_each = toset(var.bucket_names)
  
  bucket = "${var.environment}-${each.value}"
}
```

### Conditional Resources
```hcl
# Create resource only in production
resource "aws_cloudwatch_alarm" "high_cpu" {
  count = var.environment == "prod" ? 1 : 0
  
  alarm_name = "high-cpu-alarm"
  # ...
}
```

## Anti-Patterns to Avoid

❌ **Hardcoded values**
```hcl
# Bad
resource "aws_instance" "web" {
  ami = "ami-0c55b159cbfafe1f0"
}
```

❌ **No variable descriptions**
```hcl
# Bad
variable "count" {
  type = number
}
```

❌ **Untagged resources**
```hcl
# Bad - no tags
resource "aws_instance" "web" {
  ami           = var.ami
  instance_type = "t3.micro"
}
```

❌ **No version constraints**
```hcl
# Bad
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}
```

## Checklist Before Applying

- [ ] Code formatted (`terraform fmt`)
- [ ] Validation passes (`terraform validate`)
- [ ] Plan reviewed (`terraform plan`)
- [ ] Sensitive data not hardcoded
- [ ] Resources properly tagged
- [ ] Version constraints specified
- [ ] State backend configured
- [ ] Documentation updated
- [ ] Peer review completed

---

**Remember**: Infrastructure as Code is code. Apply the same standards and practices 
you use for application code.
