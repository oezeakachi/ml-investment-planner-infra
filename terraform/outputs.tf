output "vpc_id" {
  description = "The ID of the VPC : "
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = [aws_subnet.pub-a.id, aws_subnet.pub-b.id]
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = [aws_subnet.priv-a.id, aws_subnet.priv-b.id]
}

output "frontend_ecr_url" {
  description = "URL of the ECR repository for the frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_ecr_url" {
  description = "URL of the ECR repository for the backend"
  value       = aws_ecr_repository.backend.repository_url
}
