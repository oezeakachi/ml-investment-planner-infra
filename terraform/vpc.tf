# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = "true"
  enable_dns_hostnames = "true"
  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnet-a
resource "aws_subnet" "pub-a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = "true"
  availability_zone       = "${var.aws_region}a"
  tags = {
    Name = "${var.project_name}-public-a"
  }
}

# Public Subnet-b
resource "aws_subnet" "pub-b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  map_public_ip_on_launch = "true"
  availability_zone       = "${var.aws_region}b"
  tags = {
    Name = "${var.project_name}-public-b"
  }
}

# Private Subnet-a
resource "aws_subnet" "priv-a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.3.0/24"
  map_public_ip_on_launch = "true"
  availability_zone       = "${var.aws_region}a"
  tags = {
    Name = "${var.project_name}-private-a"
  }
}

# Private Subnet-b
resource "aws_subnet" "priv-b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.4.0/24"
  map_public_ip_on_launch = "true"
  availability_zone       = "${var.aws_region}b"
  tags = {
    Name = "${var.project_name}-private-b"
  }
}

# Elastic IP for NAT-a
resource "aws_eip" "nat-a" {
  domain = "vpc"
}

# Elastic IP for NAT-b
resource "aws_eip" "nat-b" {
  domain = "vpc"
}

# NAT-a Gateway
resource "aws_nat_gateway" "nat-a" {
  subnet_id     = aws_subnet.pub-a.id
  allocation_id = aws_eip.nat-a.id
  tags = {
    Name = "${var.project_name}-nat-a"
  }
}

# NAT-b Gateway
resource "aws_nat_gateway" "nat-b" {
  subnet_id     = aws_subnet.pub-b.id
  allocation_id = aws_eip.nat-b.id
  tags = {
    Name = "${var.project_name}-nat-b"
  }
}

# Public Route Table 
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "pub-a" {
  subnet_id      = aws_subnet.pub-a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "pub-b" {
  subnet_id      = aws_subnet.pub-b.id
  route_table_id = aws_route_table.public.id
}

# Private Route Table-a
resource "aws_route_table" "private-a" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-a.id
  }
  tags = {
    Name = "${var.project_name}-private-rt-a"
  }
}

resource "aws_route_table_association" "priv-a" {
  subnet_id      = aws_subnet.priv-a.id
  route_table_id = aws_route_table.private-a.id
}

# Private Route Table-b
resource "aws_route_table" "private-b" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-b.id
  }
  tags = {
    Name = "${var.project_name}-private-rt-b"
  }
}

resource "aws_route_table_association" "priv-b" {
  subnet_id      = aws_subnet.priv-b.id
  route_table_id = aws_route_table.private-b.id
}