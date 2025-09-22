# Local Variables
locals {
  cluster_name = "${var.project_name}-eks"

  # Collect private subnets from VPC
  private_subnet_ids = [
    aws_subnet.priv-a.id,
    aws_subnet.priv-b.id
  ]

  # Collect public subnets from VPC
  public_subnet_ids = [
    aws_subnet.pub-a.id,
    aws_subnet.pub-b.id
  ]
}

# EKS Cluster and Managed Node Group
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = local.cluster_name
  kubernetes_version = var.k8s_version

  vpc_id     = aws_vpc.main.id
  subnet_ids = local.private_subnet_ids

  # API endpoint access
  endpoint_public_access  = true # allow kubectl etc. from the internet
  endpoint_private_access = true # allow internal VPC access

  # IRSA (for service acount roles)
  enable_irsa = true

  # Control plane logging to CloudWatch
  create_cloudwatch_log_group            = true
  cloudwatch_log_group_retention_in_days = 30
  enabled_log_types                      = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Core EKS-managed add-ons
  addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true }
  }

  # Node Group
  eks_managed_node_groups = {
    default = {
      desired_size = var.node_desired_size
      min_size     = var.node_min_size
      max_size     = var.node_max_size

      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      subnet_ids = local.private_subnet_ids
      ami_type   = "AL2023_x86_64_STANDARD"
      disk_size  = 20

      labels = {
        role = "general"
      }
    }
  }
}

# Outputs

# output "eks_oidc_provider_arn" {
#   description = "OIDC provider ARN used for IRSA"
#   value       = module.eks.oidc_provider_arn
# }

# output "eks_nodegroup_role_name" {
#   description = "IAM role name of the default node group"
#   value       = try(module.eks.eks_managed_node_groups["default"].iam_role_name, null)
# }
