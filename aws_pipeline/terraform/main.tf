provider "aws" {
  region = var.region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "milvus-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Environment = var.environment
    Project     = "vector-search"
  }
}

module "eks" {
  source = "terraform-aws-modules/eks/aws"

  cluster_name    = "milvus-cluster"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    milvus = {
      min_size     = 2
      max_size     = 5
      desired_size = 3

      instance_types = ["r6i.2xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        Environment = var.environment
        Project     = "vector-search"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "vector-search"
  }
}

# S3 bucket for Milvus storage
resource "aws_s3_bucket" "milvus_storage" {
  bucket = "milvus-storage-${var.environment}"

  tags = {
    Environment = var.environment
    Project     = "vector-search"
  }
}

resource "aws_s3_bucket_versioning" "milvus_storage" {
  bucket = aws_s3_bucket.milvus_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

# EBS CSI Driver IAM Role
module "ebs_csi_irsa_role" {
  source = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"

  role_name             = "ebs-csi-controller"
  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
} 