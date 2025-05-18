// MongoDB Schema cho hệ thống Agri TraceChain

// Collection Users
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "email", "password", "role"],
            properties: {
                name: { bsonType: "string" },
                email: { bsonType: "string" },
                password: { bsonType: "string" },
                role: { 
                    bsonType: "string",
                    enum: ["admin", "farmer", "buyer"]
                },
                phone: { bsonType: "string" },
                address: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// Collection Products
db.createCollection("products", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "user_id"],
            properties: {
                name: { bsonType: "string" },
                description: { bsonType: "string" },
                price: { bsonType: "decimal" },
                category: { bsonType: "string" },
                image_url: { bsonType: "string" },
                user_id: { bsonType: "objectId" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Collection Batches
db.createCollection("batches", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["product_id", "qr_code"],
            properties: {
                product_id: { bsonType: "objectId" },
                qr_code: { bsonType: "string" },
                harvest_date: { bsonType: "date" },
                expiry_date: { bsonType: "date" },
                quantity: { bsonType: "int" },
                location: { bsonType: "string" },
                status: {
                    bsonType: "string",
                    enum: ["harvested", "processing", "shipping", "delivered"]
                },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// Collection TraceLogs
db.createCollection("trace_logs", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["batch_id", "action"],
            properties: {
                batch_id: { bsonType: "objectId" },
                action: { bsonType: "string" },
                timestamp: { bsonType: "date" },
                blockchain_tx: { bsonType: "string" }
            }
        }
    }
});

// Collection SupplyChainSteps
db.createCollection("supply_chain_steps", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["batch_id", "step_name"],
            properties: {
                batch_id: { bsonType: "objectId" },
                step_name: { bsonType: "string" },
                description: { bsonType: "string" },
                location: { bsonType: "string" },
                timestamp: { bsonType: "date" },
                handler_id: { bsonType: "objectId" },
                blockchain_tx: { bsonType: "string" }
            }
        }
    }
});

// Collection Orders
db.createCollection("orders", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["buyer_id", "batch_id"],
            properties: {
                buyer_id: { bsonType: "objectId" },
                batch_id: { bsonType: "objectId" },
                quantity: { bsonType: "int" },
                total_price: { bsonType: "decimal" },
                order_date: { bsonType: "date" },
                delivery_date: { bsonType: "date" },
                status: {
                    bsonType: "string",
                    enum: ["pending", "confirmed", "shipped", "delivered", "cancelled"]
                }
            }
        }
    }
});

// Collection OrderItems
db.createCollection("order_items", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["order_id", "product_id", "quantity", "unit_price", "subtotal"],
            properties: {
                order_id: { bsonType: "objectId" },
                product_id: { bsonType: "objectId" },
                batch_id: { bsonType: "objectId" },
                quantity: { bsonType: "int" },
                unit_price: { bsonType: "decimal" },
                subtotal: { bsonType: "decimal" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// Collection Reviews
db.createCollection("reviews", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["product_id", "rating"],
            properties: {
                order_id: { bsonType: "objectId" },
                user_id: { bsonType: "objectId" },
                product_id: { bsonType: "objectId" },
                rating: { bsonType: "int", minimum: 1, maximum: 5 },
                comment: { bsonType: "string" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

// Collection Payments
db.createCollection("payments", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["order_id", "user_id", "amount", "payment_method"],
            properties: {
                order_id: { bsonType: "objectId" },
                user_id: { bsonType: "objectId" },
                amount: { bsonType: "decimal" },
                payment_method: { bsonType: "string" },
                transaction_id: { bsonType: "string" },
                status: {
                    bsonType: "string",
                    enum: ["pending", "completed", "failed", "refunded"]
                },
                message: { bsonType: "string" },
                bank_name: { bsonType: "string" },
                bank_account: { bsonType: "string" },
                bank_account_name: { bsonType: "string" },
                payment_proof: { bsonType: "string" },
                payment_date: { bsonType: "date" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Collection BlockchainTransactions
db.createCollection("blockchain_transactions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["tx_hash", "related_entity", "entity_id"],
            properties: {
                tx_hash: { bsonType: "string" },
                related_entity: { bsonType: "string" },
                entity_id: { bsonType: "objectId" },
                data: { bsonType: "string" },
                timestamp: { bsonType: "date" }
            }
        }
    }
});

// Collection Carts
db.createCollection("carts", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id"],
            properties: {
                user_id: { bsonType: "objectId" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Collection CartItems
db.createCollection("cart_items", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["cart_id", "product_id", "quantity"],
            properties: {
                cart_id: { bsonType: "objectId" },
                product_id: { bsonType: "objectId" },
                batch_id: { bsonType: "objectId" },
                quantity: { bsonType: "int" },
                created_at: { bsonType: "date" },
                updated_at: { bsonType: "date" }
            }
        }
    }
});

// Collection ChatHistory
db.createCollection("chat_history", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "message"],
            properties: {
                user_id: { bsonType: "objectId" },
                message: { bsonType: "string" },
                is_user: { bsonType: "bool" },
                created_at: { bsonType: "date" },
                type: { bsonType: "string" },
                data: { bsonType: "string" }
            }
        }
    }
}); 