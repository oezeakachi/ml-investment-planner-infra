output "vpc_id" {
  description = "The ID of the VPC : "
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets : "
  value       = [aws_subnet.pub-a.id, aws_subnet.pub-b.id]
}

output "private_subnet_ids" {
  description = "IDs of the private subnets : "
  value       = [aws_subnet.priv-a.id, aws_subnet.priv-b.id]
}