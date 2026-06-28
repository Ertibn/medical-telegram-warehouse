"""
Generate realistic mock data for Ethiopian medical Telegram channels.
Creates JSON files in partitioned data lake structure.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Medical products and terms commonly discussed in Ethiopian channels
MEDICAL_PRODUCTS = [
    "Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 500mg",
    "Vitamin C 1000mg", "Multivitamin", "Aspirin 325mg",
    "Antibiotic cream", "Cough syrup", "Cold medicine",
    "Pain reliever", "Fever reducer", "Anti-diarrheal",
    "Antacid", "Laxative", "Antihistamine", "Decongestant",
    "Blood pressure monitor", "Thermometer", "Pulse oximeter",
    "First aid kit", "Bandages", "Antiseptic solution"
]

PRICES = list(range(50, 2000, 50))  # ETB prices

COSMETIC_PRODUCTS = [
    "Face cream", "Body lotion", "Shea butter", "Moisturizer",
    "Sunscreen SPF 30", "Lip balm", "Face mask", "Exfoliator",
    "Anti-aging serum", "Night cream", "Hand cream", "Body wash",
    "Face soap", "Toner", "Essence", "BB cream"
]

CHANNELS = [
    {
        "name": "CheMed",
        "username": "chemed_et",
        "type": "Medical products",
        "products": MEDICAL_PRODUCTS
    },
    {
        "name": "Lobelia Cosmetics",
        "username": "lobeliacosmeticseth",
        "type": "Cosmetics and health",
        "products": COSMETIC_PRODUCTS + ["Vitamins", "Supplements"]
    },
    {
        "name": "Tikvah Pharma",
        "username": "tikvahpharmaeth",
        "type": "Pharmaceuticals",
        "products": MEDICAL_PRODUCTS
    },
    {
        "name": "Health Plus Ethiopia",
        "username": "healthpluseth",
        "type": "Medical products",
        "products": MEDICAL_PRODUCTS + ["Medical devices"]
    },
    {
        "name": "Wellness Center",
        "username": "wellnesseth",
        "type": "Health products",
        "products": COSMETIC_PRODUCTS + MEDICAL_PRODUCTS
    }
]


def generate_message(channel, message_id, days_ago):
    """Generate a single message."""
    product = random.choice(channel["products"])
    price = random.choice(PRICES)
    
    # Message variations
    message_templates = [
        f"{product} available now - {price} ETB. Call/WhatsApp for orders.",
        f"New stock: {product}. Original quality. {price} ETB. Delivery available.",
        f"{product} - Special discount this week! {price} ETB only.",
        f"Quality assured {product}. Best price in Addis. {price} ETB.",
        f"Order now: {product}. {price} ETB. Same day delivery available.",
        f"{product} in stock. Wholesale and retail. Contact us for bulk orders.",
        f"Limited time offer: {product} at {price} ETB. Premium quality.",
        f"{product} - Trusted by thousands. Only {price} ETB. Order today!",
        f"Fresh {product} arrived. {price} ETB. Best in market.",
        f"Verified seller: {product}. {price} ETB. Money back guarantee.",
    ]
    
    message_text = random.choice(message_templates)
    
    # Timestamp
    message_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    
    # Engagement metrics
    views = random.randint(50, 2000)
    forwards = random.randint(0, 100)
    
    # Some messages have media (images of products)
    has_media = random.random() > 0.4  # 60% have media
    image_path = None
    
    if has_media:
        image_path = f"data/raw/images/{channel['name']}/{message_id}.jpg"
    
    return {
        "message_id": message_id,
        "channel_name": channel["name"],
        "channel_username": channel["username"],
        "message_date": message_date,
        "message_text": message_text,
        "has_media": has_media,
        "image_path": image_path,
        "views": views,
        "forwards": forwards,
        "media_type": "Photo" if has_media else None
    }


def generate_channel_data(channel, num_messages=200):
    """Generate messages for a channel."""
    messages = []
    
    for msg_id in range(1, num_messages + 1):
        # Distribute messages over last 30 days
        days_ago = random.randint(0, 29)
        message = generate_message(channel, msg_id, days_ago)
        messages.append(message)
    
    return messages


def save_to_data_lake(channel, messages):
    """Save messages to partitioned data lake."""
    # Partition by date (all going to today's partition for simplicity)
    today = datetime.now().strftime("%Y-%m-%d")
    partition_dir = Path("data/raw/telegram_messages") / today
    partition_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{channel['username']}.json"
    filepath = partition_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(messages)} messages to {filepath}")
    
    return filepath


def create_sample_images(channel, num_samples=5):
    """Create placeholder image files."""
    images_dir = Path("data/raw/images") / channel["name"]
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Create simple placeholder files
    for i in range(1, num_samples + 1):
        img_path = images_dir / f"{i}.jpg"
        # Write minimal JPEG header (just a placeholder)
        with open(img_path, 'wb') as f:
            # Minimal JPEG magic bytes
            f.write(b'\xff\xd8\xff\xe0')
    
    print(f"✓ Created {num_samples} placeholder images for {channel['name']}")


def main():
    """Main entry point."""
    print("=" * 70)
    print("GENERATING MOCK DATA FOR MEDICAL TELEGRAM CHANNELS")
    print("=" * 70)
    
    random.seed(42)  # For reproducibility
    
    for channel in CHANNELS:
        print(f"\nProcessing {channel['name']}...")
        
        # Generate messages
        messages = generate_channel_data(channel, num_messages=200)
        
        # Save to data lake
        save_to_data_lake(channel, messages)
        
        # Create sample images
        create_sample_images(channel, num_samples=10)
    
    print("\n" + "=" * 70)
    print("DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated data for {len(CHANNELS)} channels")
    print(f"Total messages: {len(CHANNELS) * 200}")
    print(f"Data location: data/raw/telegram_messages/")
    print(f"Images location: data/raw/images/")
    print("\nNext steps:")
    print("1. python src/load_to_postgres.py  (Load to PostgreSQL)")
    print("2. dbt run                          (Transform with dbt)")
    print("3. dbt test                         (Validate data quality)")
    print("=" * 70)


if __name__ == "__main__":
    main()
