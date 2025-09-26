output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "node_security_group_id" {
  description = "Security group ID of EKS worker nodes"
  value       = module.eks.node_security_group_id
}

output "node_group_asg_names" {
  description = "List of node group Auto Scaling Group names"
  value       = module.eks.eks_managed_node_groups["default"].node_group_autoscaling_group_names
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = [
    aws_subnet.priv-a.id,
    aws_subnet.priv-b.id
  ]
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = [
    aws_subnet.pub-a.id,
    aws_subnet.pub-b.id
  ]
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}
