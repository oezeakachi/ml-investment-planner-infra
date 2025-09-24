# Security group for ALB
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "ALB security group"
  vpc_id      = aws_vpc.main.id

  # HTTP from anywhere
  ingress {
    description = "Allow HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Egress to anywhere (ALB reaching nodes)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# ALB in public subnets
resource "aws_lb" "app" {
  name               = "${var.project_name}-alb"
  load_balancer_type = "application"
  internal           = false

  security_groups = [aws_security_group.alb_sg.id]
  subnets = [
    aws_subnet.pub-a.id,
    aws_subnet.pub-b.id
  ]

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# Target Group for FRONTEND (NodePort)
resource "aws_lb_target_group" "tg_frontend" {
  name        = "${var.project_name}-tg-fe"
  port        = var.frontend_node_port
  protocol    = "HTTP"
  target_type = "instance" # Send to EC2 nodes (NodePort)
  vpc_id      = aws_vpc.main.id

  # Health check against frontend (Next.js "/")
  health_check {
    enabled             = true
    protocol            = "HTTP"
    port                = "traffic-port"
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5
    matcher             = "200-399"
  }

  tags = {
    Name = "${var.project_name}-tg-fe"
  }
}

# Target Group for BACKEND (NodePort)
resource "aws_lb_target_group" "tg_backend" {
  name        = "${var.project_name}-tg-bd"
  port        = var.backend_node_port
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = aws_vpc.main.id

  # Health check against FastAPI docs page (returns HTTP 200)
  health_check {
    enabled             = true
    protocol            = "HTTP"
    port                = "traffic-port"
    path                = "/docs"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    interval            = 30
    timeout             = 5
    matcher             = "200-399"
  }

  tags = {
    Name = "${var.project_name}-tg-bd"
  }
}

# Listener on :80 — default to frontend
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_frontend.arn
  }
}

# Route /api/* to backend
resource "aws_lb_listener_rule" "api_path" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Attach target groups to node group ASG(s)

# Frontend TG attachment to node group's Auto Scaling Group(s)
resource "aws_autoscaling_attachment" "asg_to_tg_frontend" {
  for_each               = toset(try(module.eks.eks_managed_node_groups["default"].autoscaling_group_names, []))
  autoscaling_group_name = each.value
  lb_target_group_arn    = aws_lb_target_group.tg_frontend.arn
}

# Backend TG attachment to node group's Auto Scaling Group(s)
resource "aws_autoscaling_attachment" "asg_to_tg_backend" {
  for_each               = toset(try(module.eks.eks_managed_node_groups["default"].autoscaling_group_names, []))
  autoscaling_group_name = each.value
  lb_target_group_arn    = aws_lb_target_group.tg_backend.arn
}

# Open Node SG for NodePorts from the ALB

# Allow ALB -> Nodes on frontend NodePort
resource "aws_security_group_rule" "nodes_from_alb_frontend" {
  type                     = "ingress"
  description              = "Allow ALB to reach nodes on frontend NodePort"
  from_port                = var.frontend_node_port
  to_port                  = var.frontend_node_port
  protocol                 = "tcp"
  security_group_id        = module.eks.node_security_group_id
  source_security_group_id = aws_security_group.alb_sg.id
}

# Allow ALB -> Nodes on backend NodePort
resource "aws_security_group_rule" "nodes_from_alb_backend" {
  type                     = "ingress"
  description              = "Allow ALB to reach nodes on backend NodePort"
  from_port                = var.backend_node_port
  to_port                  = var.backend_node_port
  protocol                 = "tcp"
  security_group_id        = module.eks.node_security_group_id
  source_security_group_id = aws_security_group.alb_sg.id
}
