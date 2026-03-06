"""
scripts/seed_schemes.py
Load all government schemes from data/schemes.json into DynamoDB.
Also optionally generates Titan Embeddings for RAG (vector search).

Run: python scripts/seed_schemes.py
Run with embeddings: python scripts/seed_schemes.py --embeddings
"""

import boto3
import json
import os
import sys

REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
ROOT   = os.path.join(os.path.dirname(__file__), "..")

def load_schemes():
    path = os.path.join(ROOT, "data", "schemes.json")
    with open(path) as f:
        return json.load(f)

def seed_dynamodb(schemes):
    """Seed schemes into DynamoDB for fast keyword search."""
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table    = dynamodb.Table("welfare-schemes")

    print(f"  Seeding {len(schemes)} schemes into DynamoDB...")
    with table.batch_writer() as batch:
        for s in schemes:
            batch.put_item(Item={
                "schemeId":     s["id"],
                "category":     s["category"],
                "name":         s["name"],
                "benefit":      s["benefit"],
                "who_can_apply":s["who_can_apply"],
                "documents":    s["documents"],
                "how_to_apply": s["how_to_apply"],
                "apply_url":    s.get("apply_url", ""),
                # Lowercase blob for simple text search
                "search_text":  " ".join([
                    s["name"], s["benefit"], s["who_can_apply"],
                    s["documents"], s["category"]
                ]).lower(),
            })
    print(f"  ✅ {len(schemes)} schemes seeded to DynamoDB")

def generate_embeddings(schemes):
    """
    Generate Titan Embeddings for semantic RAG search.
    Stores embedding summary locally — connect to OpenSearch for production.
    """
    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    results = []

    print(f"  Generating embeddings for {len(schemes)} schemes...")
    for i, s in enumerate(schemes):
        text = (
            f"Scheme: {s['name']}. "
            f"Benefit: {s['benefit']}. "
            f"Who can apply: {s['who_can_apply']}. "
            f"Documents: {s['documents']}."
        )
        try:
            resp = bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=json.dumps({"inputText": text[:8000]})
            )
            embedding = json.loads(resp["body"].read())["embedding"]
            results.append({
                "schemeId": s["id"],
                "dims":     len(embedding),
                "preview":  embedding[:5],  # Save only preview
            })
            print(f"    [{i+1}/{len(schemes)}] {s['name'][:45]}... ✅")
        except Exception as e:
            print(f"    [{i+1}/{len(schemes)}] {s['name'][:45]}... ⚠️ {e}")

    out = os.path.join(ROOT, "data", "embeddings_summary.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✅ Embedding summary saved to data/embeddings_summary.json")
    print(f"  💡 For production: store full vectors in Amazon OpenSearch with k-NN")

def main():
    print("\n🇮🇳  Bharat Scheme Mitra — Seeding Knowledge Base")
    print("=" * 50)

    schemes = load_schemes()
    print(f"  Loaded {len(schemes)} schemes from data/schemes.json")

    print("\n📦 Step 1: DynamoDB (keyword search)...")
    seed_dynamodb(schemes)

    if "--embeddings" in sys.argv:
        print("\n🧠 Step 2: Titan Embeddings (semantic RAG)...")
        generate_embeddings(schemes)
    else:
        print("\n💡 For semantic RAG embeddings, run:")
        print("   python scripts/seed_schemes.py --embeddings")

    print("\n" + "=" * 50)
    print("✅ Knowledge base ready! Start the backend: cd backend && python app.py")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
