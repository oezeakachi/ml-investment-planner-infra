# Local Variables
locals {
  cluster_name = "${var.project_name}-eks"

  # Collect private subnets from VPC
  private_subnet_ids = [
    aws_subnet.priv-a.id,
    aws_subnet.priv-b.id
  ]

  # Collect public subnets from VPC (not used for nodes but kept for reference)
  public_subnet_ids = [
    aws_subnet.pub-a.id,
    aws_subnet.pub-b.id
  ]
}

# EKS Cluster and Managed Node Group
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.3.1" # <-- upgraded to latest supported module

  name                = local.cluster_name
  kubernetes_version  = var.k8s_version # <-- upgrade to latest Kubernetes version
  authentication_mode = "API"

  vpc_id     = aws_vpc.main.id
  subnet_ids = local.private_subnet_ids

  # API endpoint access
  endpoint_public_access  = true # allow kubectl etc. from the internet
  endpoint_private_access = true # allow internal VPC access

  # Adds the current caller identity as an administrator via cluster access entry
  enable_cluster_creator_admin_permissions = true

  # Enable IAM Roles for Service Accounts (IRSA)
  enable_irsa = true

  # Control plane logging to CloudWatch
  create_cloudwatch_log_group            = false
  cloudwatch_log_group_retention_in_days = 30
  enabled_log_types = [
    "api",
    "audit",
    "authenticator",
    "controllerManager",
    "scheduler"
  ]

  # Core EKS-managed add-ons — always use the most recent recommended versions
  addons = {
    coredns                = {}
    eks-pod-identity-agent = { before_compute = true }
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
  }

  # EKS Managed Node Group with Amazon Linux 2023
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

      # Required policies for worker nodes to join the cluster and pull images
      iam_role_additional_policies = {
        AmazonEKSWorkerNodePolicy          = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
        AmazonEKS_CNI_Policy               = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
        AmazonEC2ContainerRegistryReadOnly = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        CloudWatchAgentServerPolicy        = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
      }
    }
  }
}