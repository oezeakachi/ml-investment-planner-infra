variable "aws_region" {
  description = "AWS Region where resources will be created"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Prefix name for tagging and naming AWS resources"
  type        = string
  default     = "ml-inv-planner"
}

variable "k8s_version" {
  description = "Desired Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.33"
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes in the node group"
  type        = number
  default     = 2
}

variable "node_min_size" {
  description = "Minimum number of nodes in the node group"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of nodes in the node group"
  type        = number
  default     = 3
}

variable "frontend_node_port" {
  description = "Port exposed on the node"
  type        = number
  default     = 30080
}

variable "backend_node_port" {
  description = "Port exposed on the node"
  type        = number
  default     = 30081
}