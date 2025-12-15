#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get webhook URL from CloudFormation
STACK_NAME="${1:-numerolog-ai}"

echo -e "${YELLOW}🔍 Getting webhook URL from stack: ${STACK_NAME}${NC}"

WEBHOOK_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue' \
    --output text)

if [ -z "$WEBHOOK_URL" ]; then
    echo -e "${RED}❌ Could not get webhook URL. Is the stack deployed?${NC}"
    exit 1
fi

echo -e "${GREEN}Webhook URL: ${WEBHOOK_URL}${NC}"

# Load bot token from .env
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f "$(dirname "$0")/../.env" ]; then
        export $(grep TELEGRAM_BOT_TOKEN "$(dirname "$0")/../.env" | xargs)
    fi
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN not set${NC}"
    exit 1
fi

# Set webhook using Telegram API
echo -e "${YELLOW}🔗 Setting webhook...${NC}"
RESPONSE=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}")

if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo -e "${GREEN}✅ Webhook set successfully!${NC}"
    echo "$RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}❌ Failed to set webhook:${NC}"
    echo "$RESPONSE" | python3 -m json.tool
    exit 1
fi

# Get webhook info
echo ""
echo -e "${YELLOW}📋 Current webhook info:${NC}"
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | python3 -m json.tool
