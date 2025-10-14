###########################################
# Import EKS outputs from remote state
###########################################
data "terraform_remote_state" "eks" {
  backend = "s3"
  config = {
    bucket = "ml-inv-planner-one"
    key    = "eks/terraform.tfstate"
    region = "eu-west-2"
  }
}

###########################################
# Security group for ALB
###########################################
resource "aws_security_group" "alb_sg" {
  name        = "${var.project_name}-alb-sg"
  description = "ALB security group"
  vpc_id      = data.terraform_remote_state.eks.outputs.vpc_id

  ingress {
    description = "Allow HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

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

###########################################
# ALB in public subnets
###########################################
resource "aws_lb" "app" {
  name               = "${var.project_name}-alb"
  load_balancer_type = "application"
  internal           = false

  security_groups = [aws_security_group.alb_sg.id]
  subnets         = data.terraform_remote_state.eks.outputs.public_subnet_ids

  enable_deletion_protection = false

  tags = {
    Name = "${var.project_name}-alb"
  }
}

###########################################
# Target Groups
###########################################
resource "aws_lb_target_group" "tg_frontend" {
  name        = "${var.project_name}-tg-fe"
  port        = var.frontend_node_port
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.terraform_remote_state.eks.outputs.vpc_id

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

resource "aws_lb_target_group" "tg_backend" {
  name        = "${var.project_name}-tg-bd"
  port        = var.backend_node_port
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = data.terraform_remote_state.eks.outputs.vpc_id

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

###########################################
# Listener & Routing
###########################################
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg_frontend.arn
  }
}

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

###########################################
# Attach Target Groups to Nodegroup ASGs
###########################################
resource "aws_autoscaling_attachment" "asg_to_tg_frontend" {
  for_each               = toset(data.terraform_remote_state.eks.outputs.node_group_asg_names)
  autoscaling_group_name = each.value
  lb_target_group_arn    = aws_lb_target_group.tg_frontend.arn
}

resource "aws_autoscaling_attachment" "asg_to_tg_backend" {
  for_each               = toset(data.terraform_remote_state.eks.outputs.node_group_asg_names)
  autoscaling_group_name = each.value
  lb_target_group_arn    = aws_lb_target_group.tg_backend.arn
}

###########################################
# Security Group Rules for NodePorts
###########################################
resource "aws_security_group_rule" "nodes_from_alb_frontend" {
  type                     = "ingress"
  description              = "Allow ALB to reach nodes on frontend NodePort"
  from_port                = var.frontend_node_port
  to_port                  = var.frontend_node_port
  protocol                 = "tcp"
  security_group_id        = data.terraform_remote_state.eks.outputs.node_security_group_id
  source_security_group_id = aws_security_group.alb_sg.id
}

resource "aws_security_group_rule" "nodes_from_alb_backend" {
  type                     = "ingress"
  description              = "Allow ALB to reach nodes on backend NodePort"
  from_port                = var.backend_node_port
  to_port                  = var.backend_node_port
  protocol                 = "tcp"
  security_group_id        = data.terraform_remote_state.eks.outputs.node_security_group_id
  source_security_group_id = aws_security_group.alb_sg.id
}
