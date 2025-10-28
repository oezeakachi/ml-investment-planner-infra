# Local Variables
locals {
  cluster_name = "${var.project_name}-eks"

  # Collect private subnets from VPC
  private_subnet_ids = [
    aws_subnet.priv-a.id,
    aws_subnet.priv-b.id
  ]
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.3.1"

  name                = local.cluster_name
  kubernetes_version  = var.k8s_version
  authentication_mode = "API"

  vpc_id     = aws_vpc.main.id
  subnet_ids = local.private_subnet_ids

  endpoint_public_access                   = true
  endpoint_private_access                  = true
  enable_cluster_creator_admin_permissions = true
  enable_irsa                              = true

  create_cloudwatch_log_group            = false
  cloudwatch_log_group_retention_in_days = 30
  enabled_log_types                      = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Explicitly set IAM role naming to avoid prefix length issues
  iam_role_use_name_prefix = false
  iam_role_name           = "${var.project_name}-eks-cluster-role"

  addons = {
    coredns                = {}
    eks-pod-identity-agent = { before_compute = true }
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
  }

  # Managed node group 
  eks_managed_node_groups = {
    default = {
      desired_size = var.node_desired_size
      min_size     = var.node_min_size
      max_size     = var.node_max_size

      instance_types = var.node_instance_types
      ami_type       = "AL2023_x86_64_STANDARD"
      capacity_type  = "ON_DEMAND"
      disk_size      = 20
      subnet_ids     = local.private_subnet_ids

      labels = {
        role = "general"
      }

      # Disable name prefix for node group IAM role too
      iam_role_use_name_prefix = false
      iam_role_name           = "${var.project_name}-eks-node-role"

      iam_role_additional_policies = {
        AmazonEKSWorkerNodePolicy          = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
        AmazonEKS_CNI_Policy               = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
        AmazonEC2ContainerRegistryReadOnly = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        CloudWatchAgentServerPolicy        = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
      }
    }
  }
}
