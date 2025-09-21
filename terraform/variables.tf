variable "aws_region" {
  description = "AWS Region where resources will be created"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Prefix name for tagging and naming AWS resources"
  type        = string
  default     = "ml-investment-planner"
}

