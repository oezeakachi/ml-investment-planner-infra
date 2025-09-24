output "alb_dns_name" {
  description = "Application Load Balancer DNS"
  value       = aws_lb.app.dns_name
}