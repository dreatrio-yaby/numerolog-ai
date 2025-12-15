#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying Numerolog AI Bot${NC}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not configured. Please run 'aws configure' first.${NC}"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${RED}❌ SAM CLI is not installed. Please install it first:${NC}"
    echo "pip install aws-sam-cli"
    exit 1
fi

# Check for required environment variables
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  TELEGRAM_BOT_TOKEN not set. Reading from .env file...${NC}"
    if [ -f ../.env ]; then
        export $(grep -v '^#' ../.env | xargs)
    fi
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ Required environment variables not set.${NC}"
    echo "Please set TELEGRAM_BOT_TOKEN and OPENAI_API_KEY"
    exit 1
fi

# Navigate to infrastructure directory
cd "$(dirname "$0")/../infrastructure"

# Build
echo -e "${YELLOW}📦 Building...${NC}"
sam build --template template.yaml

# Deploy
echo -e "${YELLOW}🚀 Deploying...${NC}"
sam deploy \
    --parameter-overrides \
        "TelegramBotToken=$TELEGRAM_BOT_TOKEN" \
        "OpenAIApiKey=$OPENAI_API_KEY" \
    --no-confirm-changeset

# Get outputs
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Stack Outputs:${NC}"
aws cloudformation describe-stacks \
    --stack-name numerolog-ai \
    --query 'Stacks[0].Outputs' \
    --output table

# Get webhook URL
WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name numerolog-ai \
    --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue' \
    --output text)

echo ""
echo -e "${GREEN}🔗 Webhook URL: ${WEBHOOK_URL}${NC}"
echo ""
echo -e "${YELLOW}To set webhook, run:${NC}"
echo "python -m src.lambda_handler set_webhook $WEBHOOK_URL"
