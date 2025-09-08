# API Specification

Based on the REST API choice with WebSocket support, here's the comprehensive API specification for the CRM-RES platform.

## REST API Specification

```yaml
openapi: 3.0.0
info:
  title: CRM-RES WhatsApp Platform API
  version: 1.0.0
  description: REST API for Saudi restaurant WhatsApp automation platform
servers:
  - url: https://api.crm-res.com/v1
    description: Production API
  - url: https://staging-api.crm-res.com/v1
    description: Staging API

paths:
  # WhatsApp Webhook Endpoints
  /webhooks/whatsapp:
    post:
      summary: WhatsApp message webhook
      operationId: receiveWhatsAppMessage
      tags: [WhatsApp]
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WhatsAppWebhook'
      responses:
        '200':
          description: Message received
    get:
      summary: WhatsApp webhook verification
      operationId: verifyWhatsAppWebhook
      tags: [WhatsApp]
      parameters:
        - name: hub.mode
          in: query
          required: true
          schema:
            type: string
        - name: hub.verify_token
          in: query
          required: true
          schema:
            type: string
        - name: hub.challenge
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Challenge returned

  # Conversation Management
  /conversations:
    get:
      summary: List conversations
      operationId: listConversations
      tags: [Conversations]
      security:
        - bearerAuth: []
      parameters:
        - name: restaurant_id
          in: query
          schema:
            type: string
            format: uuid
        - name: status
          in: query
          schema:
            type: string
            enum: [active, escalated, resolved, abandoned]
        - name: branch_id
          in: query
          schema:
            type: string
            format: uuid
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
        - name: offset
          in: query
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: List of conversations
          content:
            application/json:
              schema:
                type: object
                properties:
                  conversations:
                    type: array
                    items:
                      $ref: '#/components/schemas/Conversation'
                  total:
                    type: integer

  /conversations/{id}:
    get:
      summary: Get conversation details
      operationId: getConversation
      tags: [Conversations]
      security:
        - bearerAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Conversation details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Conversation'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    WhatsAppWebhook:
      type: object
      properties:
        entry:
          type: array
          items:
            type: object
            properties:
              changes:
                type: array
                items:
                  type: object
                  properties:
                    value:
                      type: object
                      properties:
                        messages:
                          type: array
                        statuses:
                          type: array

    Conversation:
      type: object
      properties:
        id:
          type: string
          format: uuid
        customer_id:
          type: string
          format: uuid
        restaurant_id:
          type: string
          format: uuid
        branch_id:
          type: string
          format: uuid
        status:
          type: string
          enum: [active, escalated, resolved, abandoned]
        type:
          type: string
          enum: [feedback, order, support, general]
        ai_confidence:
          type: number
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
        started_at:
          type: string
          format: date-time

    Message:
      type: object
      properties:
        id:
          type: string
        sender:
          type: string
          enum: [customer, ai, staff]
        content:
          type: string
        timestamp:
          type: string
          format: date-time
```

## WebSocket Events (via Supabase Realtime)

```typescript
// Realtime Subscription Events
interface RealtimeEvents {
  // New conversation started
  'conversation:new': {
    conversation: Conversation;
    customer: Customer;
  };

  // Conversation status changed
  'conversation:status': {
    conversationId: string;
    oldStatus: string;
    newStatus: string;
  };

  // New message in conversation
  'message:new': {
    conversationId: string;
    message: Message;
  };

  // AI confidence dropped (needs attention)
  'ai:low_confidence': {
    conversationId: string;
    confidence: number;
    suggestedAction: string;
  };

  // New order placed
  'order:new': {
    order: Order;
    branchId: string;
  };

  // Negative feedback received
  'feedback:negative': {
    feedback: Feedback;
    requiresFollowup: boolean;
  };
}

// Supabase Realtime Channel Setup
const channel = supabase
  .channel('restaurant_updates')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'conversations',
    filter: `restaurant_id=eq.${restaurantId}`
  }, handleNewConversation)
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'conversations',
    filter: `restaurant_id=eq.${restaurantId}`
  }, handleConversationUpdate)
  .subscribe();
```
